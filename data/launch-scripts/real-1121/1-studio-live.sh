#!/usr/bin/env bash
# One iPhone in the right hand, CUDA Live, 11/21 defaults. Phone: PC <lan-ip-1> (Unitree Wi-Fi), UDP 9002, Right arm.
set -euo pipefail
RUN_ID="$(date +%Y%m%d-%H%M%S)-g1-supported-one-iphone"
BASE="$HOME/shape-msi/runs-1121/$RUN_ID"; mkdir -p "$BASE"; echo "$BASE" > "$HOME/shape-msi/relay/real-1121/current-run"
cd "$HOME/shape-msi/source-live-1121"
PYTHONPATH="$PWD/src" exec "$HOME/shape-msi/venv-gpu/bin/python" -m g1_airpots serve \
  --profile one_phone_right_hand --backend imucoco --model-device cuda --host 0.0.0.0 --port 8765 --udp-port 9002 \
  --retarget --retarget-scope arms --sonic-live --sonic-delay 0.35 --sonic-endpoint tcp://127.0.0.1:5556 \
  --output "$BASE/recording" 2>&1 | tee "$BASE/studio.log"
