#!/usr/bin/env bash
# Download the FiveThirtyEight/Clemson IRA troll-tweet dataset (~600MB, 13 CSVs)
# into validation/data/. Skips files that already exist.
set -euo pipefail

DATA_DIR="$(cd "$(dirname "$0")" && pwd)/data"
BASE_URL="https://raw.githubusercontent.com/fivethirtyeight/russian-troll-tweets/master"

mkdir -p "$DATA_DIR"

for i in $(seq 1 13); do
    file="IRAhandle_tweets_${i}.csv"
    dest="$DATA_DIR/$file"
    if [[ -s "$dest" ]]; then
        echo "✓ $file already present, skipping"
        continue
    fi
    echo "↓ $file"
    curl -fL --retry 3 --progress-bar -o "$dest.partial" "$BASE_URL/$file"
    mv "$dest.partial" "$dest"
done

echo "Done. Files in $DATA_DIR:"
ls -lh "$DATA_DIR"/IRAhandle_tweets_*.csv
