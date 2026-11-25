#!/usr/bin/env bash
# DEVELOPMENT Live, three phones (L, R iPhone; P Galaxy), pose mode, b2a59f1 (11/21 Stage 1 source). Not a judged Guided trial.
set -euo pipefail
ROOT="$HOME/shape-msi"; SOURCE="$ROOT/source-stage1-b2a59f1"
RUN_ID="$(date +%Y%m%d-%H%M%S)-live-three-phone-dev"; RUN_DIR="$ROOT/runs-1122/$RUN_ID"; mkdir -p "$RUN_DIR"
printf '%s\n' "$RUN_DIR" > "$ROOT/relay/real-1122/current-run"
printf 'RUN_ID=%s\nSource commit=%s\nProfile=three_phone\nMode=pose (development)\n' "$RUN_ID" "$(git -C "$SOURCE" rev-parse --short HEAD)"
cd "$SOURCE"
PYTHONPATH="$SOURCE/src" "$ROOT/venv-gpu/bin/python" -m g1_airpots serve \
  --profile three_phone --backend imucoco --model-device cuda --host 0.0.0.0 --port 8765 --udp-port 9002 \
  --retarget --retarget-scope arms --sonic-live --sonic-delay 0.35 --sonic-endpoint tcp://127.0.0.1:5556 \
  --output "$RUN_DIR/recording" 2>&1 | tee "$RUN_DIR/studio-live.log"
