#!/usr/bin/env bash
set -euxo pipefail

cat water-build/chunk_*.b64 > ishrab_v3.tar.gz.b64
base64 -d ishrab_v3.tar.gz.b64 > ishrab_v3.tar.gz
gzip -t ishrab_v3.tar.gz
tar -xzf ishrab_v3.tar.gz
patch -p1 -d ishrab_v3 < water-build/v3-fix.patch

cat water-build/v4fix06hex_0.txt water-build/v4fix06hex_1.txt \
  | tr -d '\r\n ' \
  | python3 -c 'import sys; sys.stdout.buffer.write(bytes.fromhex(sys.stdin.read()))' \
  > corrected-06.b64
test "$(wc -c < corrected-06.b64)" = "4000"
: > v4-ai.patch.gz.b64
for i in $(seq -w 0 19); do
  f="water-build/v4ai_${i}.b64"
  if [ "$i" = "06" ]; then f="corrected-06.b64"; fi
  tr -d '\r\n ' < "$f" >> v4-ai.patch.gz.b64
done
test "$(wc -c < v4-ai.patch.gz.b64)" = "76216"
base64 -d v4-ai.patch.gz.b64 > v4-ai.patch.gz
gzip -t v4-ai.patch.gz
gzip -dc v4-ai.patch.gz > v4-ai.patch
test "$(sha256sum v4-ai.patch | awk '{print $1}')" = "5522d79bed4abd2fd8ad784546ccc937ffb0da6780f39b589fd968118f00fb24"
patch -p1 -d ishrab_v3 < v4-ai.patch

cat water-build-v6/v6code_??.b64 | tr -d '\r\n ' > v6-code.patch.gz.b64
test "$(wc -c < v6-code.patch.gz.b64)" = "29168"
base64 -d v6-code.patch.gz.b64 > v6-code.patch.gz
gzip -t v6-code.patch.gz
gzip -dc v6-code.patch.gz > v6-code.patch
test "$(sha256sum v6-code.patch | awk '{print $1}')" = "889ae1696ba0704000e7717fd2f0f4f31121b92a4e9e13bb26b86dd256ae87d5"
patch -p1 -d ishrab_v3 < v6-code.patch

rm -f ishrab_v3/app/src/main/assets/local_health_ai_v1.json
test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/LearningMemory.java
test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/QuickStatusNotification.java
test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/QuickLogReceiver.java
grep -q 'com.ishrab.smarthealth.ai.memory' ishrab_v3/app/build.gradle
grep -q "versionName '6.0'" ishrab_v3/app/build.gradle

python3 -m pip install --disable-pip-version-check --quiet scikit-learn==1.8.0
MODEL="ishrab_v3/app/src/main/assets/local_health_ai_v2.json"
python3 water-build-v6/train_model.py "$MODEL" | tee train-v6.log
python3 - <<'PY'
import json
from pathlib import Path
p=Path('ishrab_v3/app/src/main/assets/local_health_ai_v2.json')
m=json.loads(p.read_text())
assert m['training_examples']==10000
assert m['intent_count']==20
assert len(m['classes'])==20
assert len(m['vocabulary'])==3200
assert len(m['idf'])==3200
assert len(m['coefficients'])==20
assert all(len(row)==3200 for row in m['coefficients'])
assert m['learning']['persistent_memory'] is True
assert m['learning']['automatic_forgetting'] is False
print('V6 model audit passed',p.stat().st_size,m['validation_accuracy'])
PY
sha256sum "$MODEL" > trained-model.sha256
stat -c '%s' "$MODEL" > trained-model.size
