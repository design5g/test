#!/usr/bin/env bash
set -euo pipefail

URL="https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q8_0.gguf?download=true"
EXPECTED_SIZE=639446688
EXPECTED_SHA256="9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
CHUNK_SIZE=$((16 * 1024 * 1024))
OUTPUT=${1:?output path required}
PARTS_DIR="${OUTPUT}.parts"

mkdir -p "$(dirname "$OUTPUT")" "$PARTS_DIR"
rm -f "$OUTPUT"

index=0
start=0
while [ "$start" -lt "$EXPECTED_SIZE" ]; do
  end=$((start + CHUNK_SIZE - 1))
  if [ "$end" -ge "$EXPECTED_SIZE" ]; then
    end=$((EXPECTED_SIZE - 1))
  fi
  expected=$((end - start + 1))
  part=$(printf '%s/part-%05d' "$PARTS_DIR" "$index")

  if [ -f "$part" ] && [ "$(stat -c%s "$part")" = "$expected" ]; then
    echo "Reusing chunk $index bytes=$start-$end"
  else
    rm -f "$part" "$part.tmp"
    ok=0
    for attempt in $(seq 1 12); do
      echo "Downloading chunk $index bytes=$start-$end attempt=$attempt"
      if curl --location --fail --silent --show-error \
          --connect-timeout 45 --max-time 900 \
          --retry 5 --retry-all-errors --retry-delay 5 \
          --range "$start-$end" \
          --output "$part.tmp" \
          "${URL}&range_nonce=${start}_${attempt}"; then
        actual=$(stat -c%s "$part.tmp" 2>/dev/null || echo 0)
        if [ "$actual" = "$expected" ]; then
          mv "$part.tmp" "$part"
          ok=1
          break
        fi
        echo "Unexpected chunk size: expected=$expected actual=$actual"
      fi
      rm -f "$part.tmp"
      sleep 8
    done
    test "$ok" = "1"
  fi

  index=$((index + 1))
  start=$((end + 1))
done

for part in "$PARTS_DIR"/part-*; do
  cat "$part" >> "$OUTPUT"
done

test "$(stat -c%s "$OUTPUT")" = "$EXPECTED_SIZE"
test "$(sha256sum "$OUTPUT" | awk '{print $1}')" = "$EXPECTED_SHA256"
echo "Verified Qwen model: $(ls -lh "$OUTPUT")"
