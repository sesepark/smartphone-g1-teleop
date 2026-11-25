#!/usr/bin/env bash
# PHYSICAL G1. Run only by the on-site controller operator, after the checklist in README-ko.md.
# Agents must not run this script.
set -euo pipefail
if ps -eo args | grep -qE '^[^ ]*g1_deploy_onnx_ref '; then echo "A SONIC controller is already running. Stop it first."; exit 1; fi
[ "$(cat /sys/class/net/enp4s0/carrier 2>/dev/null)" = 1 ] || { echo "enp4s0 has no link."; exit 1; }
ip -4 -br addr show dev enp4s0 | grep -q '192.168.123.' || { echo "enp4s0 has no 192.168.123.x address."; exit 1; }
BASE="$(cat "$HOME/shape-msi/relay/real-1121/current-run")"
echo "Run directory: $BASE"
echo "Checklist: gantry attached, dedicated E-stop operator at the physical stop, robot in the on-site approved mode,"
echo "1.5 m area clear, Studio tracking with calibration done, video recording started."
read -r -p "Type REAL to start the physical controller: " answer
[ "$answer" = REAL ] || { echo "Cancelled."; exit 1; }
export LD_LIBRARY_PATH=~/.local/opt/TensorRT-10.13.3.9/lib:/usr/local/cuda-12.9/lib64:/opt/onnxruntime/lib
cd "$HOME/shape-msi/source-live-1121"
PYTHONPATH="$PWD/src" "$HOME/SHAPE_g1_airpots/.venv/bin/python" -m g1_airpots sonic-controller \
  --repo ~/shape/SONIC/sonic --mode real --interface enp4s0 --prebuilt \
  --capture-url http://127.0.0.1:8765 --zmq-port 5556 --watchdog-timeout 0.5 \
  --report "$BASE/real-controller.json" 2>&1 | tee "$BASE/real-controller-terminal.log"
