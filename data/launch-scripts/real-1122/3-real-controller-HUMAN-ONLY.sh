#!/usr/bin/env bash
# PHYSICAL G1. Only the on-site controller operator may run this script.
set -euo pipefail
ROOT="$HOME/shape-msi"
RELAY_DIR="$ROOT/relay/real-1122"
RUN_FILE="$RELAY_DIR/current-run"

if ps -eo args | grep -qE '^[^ ]*g1_deploy_onnx_ref '; then
  echo "A SONIC controller is already running. Stop it first."
  exit 1
fi
[ "$(cat /sys/class/net/enp4s0/carrier 2>/dev/null)" = 1 ] || { echo "enp4s0 has no link."; exit 1; }
ip -4 -br addr show dev enp4s0 | grep -q '192.168.123.' || { echo "enp4s0 has no 192.168.123.x address."; exit 1; }
[ -f "$RUN_FILE" ] || { echo "Start 1-studio-live.sh first; no current run is recorded."; exit 1; }
BASE="$(cat "$RUN_FILE")"
case "$BASE" in "$ROOT"/runs-1122/*) ;; *) echo "Current run is outside runs-1122."; exit 1 ;; esac
echo "Run directory: $BASE"
echo "Source: source-stage1-b2a59f1 (b2a59f1) · profile: one_phone_right_hand · mode: pose"
echo "Checklist: approved gantry attached, dedicated physical E-stop operator, on-site robot mode verified,"
echo "1.5 m area clear, Studio calibrated and tracking, and video recording started."
read -r -p "Type REAL to start the physical controller: " answer
[ "$answer" = REAL ] || { echo "Cancelled."; exit 1; }

export LD_LIBRARY_PATH=~/.local/opt/TensorRT-10.13.3.9/lib:/usr/local/cuda-12.9/lib64:/opt/onnxruntime/lib
cd "$ROOT/source-stage1-b2a59f1"
PYTHONPATH="$PWD/src" "$HOME/SHAPE_g1_airpots/.venv/bin/python" -m g1_airpots sonic-controller \
  --repo ~/shape/SONIC/sonic --mode real --interface enp4s0 --prebuilt \
  --capture-url http://127.0.0.1:8765 --zmq-port 5556 --watchdog-timeout 0.5 \
  --report "$BASE/real-controller.json" 2>&1 | tee "$BASE/real-controller-terminal.log"
