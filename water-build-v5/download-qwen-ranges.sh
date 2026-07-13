#!/usr/bin/env bash
set -euo pipefail

URL="https://www.modelscope.cn/models/Qwen/Qwen3-0.6B-GGUF/resolve/master/Qwen3-0.6B-Q8_0.gguf"
EXPECTED_SIZE=639446688
EXPECTED_SHA256="9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
CHUNK_SIZE=$((16 * 1024 * 1024))
PARALLEL_DOWNLOADS=8
OUTPUT=${1:?output path required}
PARTS_DIR="${OUTPUT}.parts"
JOBS_FILE="${PARTS_DIR}/jobs.txt"

mkdir -p "$(dirname "$OUTPUT")" "$PARTS_DIR"
rm -f "$OUTPUT" "$JOBS_FILE"

index=0
start=0
while [ "$start" -lt "$EXPECTED_SIZE" ]; do
  end=$((start + CHUNK_SIZE - 1))
  if [ "$end" -ge "$EXPECTED_SIZE" ]; then
    end=$((EXPECTED_SIZE - 1))
  fi
  expected=$((end - start + 1))
  part=$(printf '%s/part-%05d' "$PARTS_DIR" "$index")
  printf '%s\t%s\t%s\t%s\t%s\n' "$index" "$start" "$end" "$expected" "$part" >> "$JOBS_FILE"
  index=$((index + 1))
  start=$((end + 1))
done

download_one() {
  local index=$1 start=$2 end=$3 expected=$4 part=$5
  if [ -f "$part" ] && [ "$(stat -c%s "$part")" = "$expected" ]; then
    echo "Reusing chunk $index bytes=$start-$end"
    return 0
  fi
  rm -f "$part" "$part.tmp"
  local attempt actual
  for attempt in $(seq 1 12); do
    echo "Downloading chunk $index bytes=$start-$end attempt=$attempt"
    if curl --location --fail --silent --show-error \
        --connect-timeout 45 --max-time 900 \
        --retry 5 --retry-all-errors --retry-delay 5 \
        --range "$start-$end" \
        --output "$part.tmp" \
        "$URL"; then
      actual=$(stat -c%s "$part.tmp" 2>/dev/null || echo 0)
      if [ "$actual" = "$expected" ]; then
        mv "$part.tmp" "$part"
        echo "Completed chunk $index"
        return 0
      fi
      echo "Unexpected chunk $index size: expected=$expected actual=$actual"
    fi
    rm -f "$part.tmp"
    sleep 8
  done
  echo "Failed chunk $index" >&2
  return 1
}
export -f download_one
export URL

xargs -P "$PARALLEL_DOWNLOADS" -n 5 bash -c 'download_one "$@"' _ < "$JOBS_FILE"

for part in "$PARTS_DIR"/part-*; do
  cat "$part" >> "$OUTPUT"
done

test "$(stat -c%s "$OUTPUT")" = "$EXPECTED_SIZE"
test "$(sha256sum "$OUTPUT" | awk '{print $1}')" = "$EXPECTED_SHA256"
echo "Verified Qwen model: $(ls -lh "$OUTPUT")"
