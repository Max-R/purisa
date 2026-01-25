"""
Inflammatory content detection using Detoxify ML model.

This module provides ML-based detection of toxic/inflammatory language in comments
using the Detoxify library, which is trained on the Jigsaw toxicity dataset.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Lazy load Detoxify to avoid import-time model loading
_detoxify_model = None


@dataclass
class InflammatoryMatch:
    """Result of inflammatory content analysis."""
    is_inflammatory: bool
    severity_score: float              # 0.0-1.0 (max of all toxicity scores)
    toxicity_scores: Dict[str, float]  # Full Detoxify output
    triggered_categories: List[str]    # Categories above threshold


class DetoxifyInflammatoryDetector:
    """
    ML-based inflammatory detection using Detoxify.

    Uses the 'original-small' model (Albert-based) for efficiency.
    Achieves 98.28% AUC on Jigsaw toxicity dataset.

    Detoxify categories:
    - toxic: General toxicity
    - severe_toxic: Highly toxic content
    - obscene: Profanity/obscenity
    - threat: Threatening language
    - insult: Insulting language
    - identity_hate: Identity-based attacks
    """

    def __init__(
        self,
        model_name: str = 'original-small',
        threshold: float = 0.5,
        device: str = 'cpu'
    ):
        """
        Initialize Detoxify detector.

        Args:
            model_name: 'original-small' (fast) or 'original' (more accurate)
                       or 'unbiased' (reduced demographic bias)
            threshold: Score threshold for flagging (0.0-1.0)
            device: 'cpu' or 'cuda' for GPU acceleration
        """
        self.threshold = threshold
        self.model_name = model_name
        self.device = device
        self._model = None
        logger.info(f"DetoxifyInflammatoryDetector configured with model={model_name}, threshold={threshold}, device={device}")

    @property
    def model(self):
        """Lazy load the Detoxify model on first use."""
        if self._model is None:
            try:
                from detoxify import Detoxify
                logger.info(f"Loading Detoxify model: {self.model_name}")
                self._model = Detoxify(self.model_name, device=self.device)
                logger.info(f"Detoxify model loaded successfully")
            except ImportError:
                logger.error("Detoxify not installed. Install with: pip install detoxify")
                raise ImportError(
                    "Detoxify library not found. Install with: pip install detoxify"
                )
        return self._model

    def analyze(self, text: str) -> InflammatoryMatch:
        """
        Analyze text for inflammatory/toxic content.

        Args:
            text: Text to analyze

        Returns:
            InflammatoryMatch with toxicity scores and flags
        """
        if not text or not text.strip():
            return InflammatoryMatch(
                is_inflammatory=False,
                severity_score=0.0,
                toxicity_scores={},
                triggered_categories=[]
            )

        # Get predictions from Detoxify
        scores = self.model.predict(text)

        # Find categories above threshold
        triggered = [
            category for category, score in scores.items()
            if score >= self.threshold
        ]

        # Severity is the max score across all categories
        severity = max(scores.values()) if scores else 0.0

        return InflammatoryMatch(
            is_inflammatory=len(triggered) > 0,
            severity_score=float(severity),
            toxicity_scores={k: float(v) for k, v in scores.items()},
            triggered_categories=triggered
        )

    def analyze_batch(self, texts: List[str]) -> List[InflammatoryMatch]:
        """
        Analyze multiple texts efficiently (batched inference).

        Args:
            texts: List of texts to analyze

        Returns:
            List of InflammatoryMatch results
        """
        if not texts:
            return []

        # Filter out empty texts but keep track of indices
        valid_indices = []
        valid_texts = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_indices.append(i)
                valid_texts.append(text)

        # Create results list with default empty matches
        results = [
            InflammatoryMatch(
                is_inflammatory=False,
                severity_score=0.0,
                toxicity_scores={},
                triggered_categories=[]
            )
            for _ in texts
        ]

        if not valid_texts:
            return results

        # Detoxify supports batch prediction
        all_scores = self.model.predict(valid_texts)

        # Process each valid text's scores
        for idx, orig_idx in enumerate(valid_indices):
            # Extract scores for this text
            # When batch predicting, scores are arrays
            if isinstance(list(all_scores.values())[0], (list, tuple)):
                text_scores = {
                    category: float(scores[idx])
                    for category, scores in all_scores.items()
                }
            else:
                # Single text case
                text_scores = {k: float(v) for k, v in all_scores.items()}

            triggered = [
                category for category, score in text_scores.items()
                if score >= self.threshold
            ]

            severity = max(text_scores.values()) if text_scores else 0.0

            results[orig_idx] = InflammatoryMatch(
                is_inflammatory=len(triggered) > 0,
                severity_score=float(severity),
                toxicity_scores=text_scores,
                triggered_categories=triggered
            )

        return results


# Singleton instance for reuse
_detector_instance: Optional[DetoxifyInflammatoryDetector] = None


def get_inflammatory_detector(
    model_name: str = 'original-small',
    threshold: float = 0.5,
    device: str = 'cpu',
    force_new: bool = False
) -> DetoxifyInflammatoryDetector:
    """
    Get inflammatory detector instance (singleton pattern).

    Args:
        model_name: Detoxify model to use
        threshold: Score threshold for flagging
        device: 'cpu' or 'cuda'
        force_new: If True, create a new instance instead of reusing

    Returns:
        DetoxifyInflammatoryDetector instance
    """
    global _detector_instance

    if force_new or _detector_instance is None:
        _detector_instance = DetoxifyInflammatoryDetector(
            model_name=model_name,
            threshold=threshold,
            device=device
        )

    return _detector_instance
