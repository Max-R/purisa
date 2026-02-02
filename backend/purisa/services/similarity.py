"""
Text and URL similarity functions for coordination detection.

Uses TF-IDF vectorization and cosine similarity for text comparison.
"""
import re
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result of a similarity comparison between two items."""
    item1_id: str
    item2_id: str
    similarity_score: float  # 0.0 to 1.0
    similarity_type: str  # 'text', 'url', 'hashtag'
    evidence: Dict  # Supporting data


def extract_urls(text: str) -> Set[str]:
    """
    Extract URLs from text content.

    Args:
        text: Text content to extract URLs from

    Returns:
        Set of normalized URLs found in text
    """
    if not text:
        return set()

    # URL regex pattern
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text, re.IGNORECASE)

    # Normalize URLs: remove trailing punctuation, lowercase domain
    normalized = set()
    for url in urls:
        # Remove trailing punctuation
        url = url.rstrip('.,;:!?)\'"]')
        try:
            parsed = urlparse(url)
            # Normalize: lowercase domain, keep path
            normalized_url = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}"
            if parsed.query:
                normalized_url += f"?{parsed.query}"
            normalized.add(normalized_url)
        except Exception:
            normalized.add(url.lower())

    return normalized


def extract_hashtags(text: str) -> Set[str]:
    """
    Extract hashtags from text content.

    Args:
        text: Text content to extract hashtags from

    Returns:
        Set of lowercase hashtags (without # symbol)
    """
    if not text:
        return set()

    # Match hashtags (alphanumeric and underscore)
    hashtag_pattern = r'#(\w+)'
    hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)

    return {tag.lower() for tag in hashtags}


def preprocess_text(text: str) -> str:
    """
    Preprocess text for similarity comparison.

    - Lowercase
    - Remove URLs
    - Remove hashtags
    - Remove mentions
    - Remove extra whitespace

    Args:
        text: Raw text content

    Returns:
        Preprocessed text for comparison
    """
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove hashtags
    text = re.sub(r'#\w+', '', text)

    # Remove mentions (@username)
    text = re.sub(r'@\w+', '', text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text


class TextSimilarityCalculator:
    """
    Calculate text similarity using TF-IDF and cosine similarity.

    Designed for batch processing of posts within a time window.
    """

    def __init__(self, min_text_length: int = 10, similarity_threshold: float = 0.8):
        """
        Initialize the calculator.

        Args:
            min_text_length: Minimum text length to consider for comparison
            similarity_threshold: Threshold above which texts are considered similar
        """
        self.min_text_length = min_text_length
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # Unigrams and bigrams
            min_df=1,
            max_df=0.95,
            stop_words='english'
        )

    def find_similar_pairs(
        self,
        posts: List[Tuple[str, str, str]],  # (post_id, account_id, content)
        threshold: Optional[float] = None
    ) -> List[SimilarityResult]:
        """
        Find pairs of posts with similar text content.

        Args:
            posts: List of (post_id, account_id, content) tuples
            threshold: Optional override for similarity threshold

        Returns:
            List of SimilarityResult for pairs above threshold
        """
        if threshold is None:
            threshold = self.similarity_threshold

        if len(posts) < 2:
            return []

        # Preprocess and filter posts
        valid_posts = []
        for post_id, account_id, content in posts:
            processed = preprocess_text(content)
            if len(processed) >= self.min_text_length:
                valid_posts.append((post_id, account_id, processed, content))

        if len(valid_posts) < 2:
            return []

        # Extract just the processed text for vectorization
        texts = [p[2] for p in valid_posts]

        try:
            # Fit and transform
            tfidf_matrix = self.vectorizer.fit_transform(texts)

            # Calculate pairwise cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # Find pairs above threshold (excluding self-comparisons)
            results = []
            n = len(valid_posts)
            for i in range(n):
                for j in range(i + 1, n):
                    score = similarity_matrix[i, j]
                    if score >= threshold:
                        # Don't pair posts from the same account
                        if valid_posts[i][1] != valid_posts[j][1]:
                            results.append(SimilarityResult(
                                item1_id=valid_posts[i][0],
                                item2_id=valid_posts[j][0],
                                similarity_score=float(score),
                                similarity_type='text',
                                evidence={
                                    'account1': valid_posts[i][1],
                                    'account2': valid_posts[j][1],
                                    'text1_preview': valid_posts[i][3][:100],
                                    'text2_preview': valid_posts[j][3][:100],
                                }
                            ))

            return results

        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return []


def find_url_sharing_pairs(
    posts: List[Tuple[str, str, str]]  # (post_id, account_id, content)
) -> List[SimilarityResult]:
    """
    Find pairs of posts that share the same URLs.

    Args:
        posts: List of (post_id, account_id, content) tuples

    Returns:
        List of SimilarityResult for posts sharing URLs
    """
    if len(posts) < 2:
        return []

    # Extract URLs from each post
    post_urls: Dict[str, Tuple[str, Set[str]]] = {}  # post_id -> (account_id, urls)
    for post_id, account_id, content in posts:
        urls = extract_urls(content)
        if urls:
            post_urls[post_id] = (account_id, urls)

    if len(post_urls) < 2:
        return []

    # Build URL -> posts index
    url_to_posts: Dict[str, List[Tuple[str, str]]] = {}  # url -> [(post_id, account_id)]
    for post_id, (account_id, urls) in post_urls.items():
        for url in urls:
            if url not in url_to_posts:
                url_to_posts[url] = []
            url_to_posts[url].append((post_id, account_id))

    # Find pairs sharing URLs
    results = []
    seen_pairs = set()

    for url, posts_with_url in url_to_posts.items():
        if len(posts_with_url) < 2:
            continue

        # Create pairs from posts sharing this URL
        for i, (post1_id, account1_id) in enumerate(posts_with_url):
            for post2_id, account2_id in posts_with_url[i + 1:]:
                # Skip same account
                if account1_id == account2_id:
                    continue

                # Skip duplicate pairs
                pair_key = tuple(sorted([post1_id, post2_id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                results.append(SimilarityResult(
                    item1_id=post1_id,
                    item2_id=post2_id,
                    similarity_score=1.0,  # URL match is exact
                    similarity_type='url',
                    evidence={
                        'account1': account1_id,
                        'account2': account2_id,
                        'shared_url': url,
                    }
                ))

    return results


def find_hashtag_overlap_pairs(
    posts: List[Tuple[str, str, str]],  # (post_id, account_id, content)
    min_overlap: int = 2
) -> List[SimilarityResult]:
    """
    Find pairs of posts with significant hashtag overlap.

    Args:
        posts: List of (post_id, account_id, content) tuples
        min_overlap: Minimum number of shared hashtags

    Returns:
        List of SimilarityResult for posts with hashtag overlap
    """
    if len(posts) < 2:
        return []

    # Extract hashtags from each post
    post_hashtags: Dict[str, Tuple[str, Set[str]]] = {}  # post_id -> (account_id, hashtags)
    for post_id, account_id, content in posts:
        hashtags = extract_hashtags(content)
        if len(hashtags) >= min_overlap:
            post_hashtags[post_id] = (account_id, hashtags)

    if len(post_hashtags) < 2:
        return []

    # Find pairs with overlapping hashtags
    results = []
    post_ids = list(post_hashtags.keys())

    for i, post1_id in enumerate(post_ids):
        account1_id, hashtags1 = post_hashtags[post1_id]
        for post2_id in post_ids[i + 1:]:
            account2_id, hashtags2 = post_hashtags[post2_id]

            # Skip same account
            if account1_id == account2_id:
                continue

            overlap = hashtags1 & hashtags2
            if len(overlap) >= min_overlap:
                # Calculate Jaccard similarity
                union = hashtags1 | hashtags2
                similarity = len(overlap) / len(union) if union else 0

                results.append(SimilarityResult(
                    item1_id=post1_id,
                    item2_id=post2_id,
                    similarity_score=similarity,
                    similarity_type='hashtag',
                    evidence={
                        'account1': account1_id,
                        'account2': account2_id,
                        'shared_hashtags': list(overlap),
                        'overlap_count': len(overlap),
                    }
                ))

    return results
