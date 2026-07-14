#!/usr/bin/env bash
set -euxo pipefail

bash water-build-v6/prepare_v6.sh 2>&1 | tee prepare-v6-for-v7.log

cat water-build-v7/v7p_??.b64 | tr -d '\r\n ' > v7.patch.gz.b64
test "$(wc -c < v7.patch.gz.b64)" = "51420"
test "$(sha256sum v7.patch.gz.b64 | awk '{print $1}')" = "9a44c3f01f254e98cc4b6889778ef5303ad6f920c484c02cdc4fb65d74e24717"
base64 -d v7.patch.gz.b64 > v7.patch.gz
gzip -t v7.patch.gz
test "$(sha256sum v7.patch.gz | awk '{print $1}')" = "8364e3aa452070c89e3e478e9037d78cab6943131e2c6261f793b5e9b5884f77"
gzip -dc v7.patch.gz > v7.patch
test "$(sha256sum v7.patch | awk '{print $1}')" = "d35442fcc21357371f9c99fd3327eb19830dbb70ce72501b7eb4d11ff10a7b2a"
patch -p1 -d ishrab_v3 < v7.patch

test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/RealLlmEngine.java
test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/MedicalKnowledge.java
test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/SelfModelEngine.java
test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/HealthGraphEngine.java
test -f ishrab_v3/app/src/main/java/com/ishrab/smarthealth/SafetyCore.java
test -f ishrab_v3/app/src/main/java/com/arm/aichat/internal/InferenceEngineImpl.java
test -f ishrab_v3/app/src/main/cpp/CMakeLists.txt
grep -Fq "applicationId 'com.ishrab.smarthealth.ai.v7'" ishrab_v3/app/build.gradle
grep -Fq "versionName '7.0'" ishrab_v3/app/build.gradle
grep -Fq 'android.permission.INTERNET' ishrab_v3/app/src/main/AndroidManifest.xml
grep -Fq 'EXPECTED_UNITS = 100_000' ishrab_v3/app/src/main/java/com/ishrab/smarthealth/MedicalKnowledge.java
grep -Fq 'Qwen3-0.6B-Q8_0.gguf' ishrab_v3/app/src/main/java/com/ishrab/smarthealth/ModelManager.java
