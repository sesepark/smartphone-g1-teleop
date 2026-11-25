# Experiment logs

Logs of the two real-robot demonstrations in the paper and the metrics behind Table 1. Everything here was copied from the team's raw run archive of 2026-11-22 (`SHAPE_G1_MSI_runs_20261122-1815.tar`, SHA-256 `6fc4377a…f861`) by [`tools/prepare_public_data.py`](../tools/prepare_public_data.py). [`SHA256SUMS`](SHA256SUMS) lists every file.

## Folders

| Folder | What it is |
| --- | --- |
| [`runs/20261121-215716-g1-supported-one-iphone`](runs/20261121-215716-g1-supported-one-iphone) | 1st demonstration, 2026-11-21 21:57–22:19 KST: one iOS phone in the right hand, G1 on a gantry, three controller sessions |
| [`runs/20261122-174632-live-three-phone-dev`](runs/20261122-174632-live-three-phone-dev) | 2nd demonstration, last three-phone run (run 7), 2026-11-22 17:46–17:57 KST |
| [`runs/other-three-phone-runs`](runs/other-three-phone-runs) | controller results of runs 1, 2 and 6 on 2026-11-22 (no recordings) |
| [`launch-scripts`](launch-scripts) | the scripts that started the estimation server and the SONIC controller on the laptop |
| [`one-arm-replay`](one-arm-replay) | metrics of the offline AR elbow replay (Table 1) |

## Files in a run folder

All times in `raw.jsonl`, `motion.jsonl` and `sonic-live.json` are the laptop's monotonic clock in seconds, so they share one time base within a run. `.xz` files open with `xz -d` or Python's `lzma`.

| File | Contents |
| --- | --- |
| `recording/raw.jsonl.xz` | every UDP packet the laptop received: `receive_time` plus the phone `packet` (`sample` = IMU quaternion, acceleration and gyro; `ar_pose` = ARKit/ARCore pose; `sync_result` = clock sync; `calibration_event`; `locomotion` = joystick state, unused here) |
| `recording/motion.jsonl.xz` (run 7) | one line per 60 Hz estimate: `t` (sample time), `joints` (24 SMPL joint positions, m, y up), `pose_axis_angle`, `robot` (G1 `joint_pos` in the order of `session.json` `robot.joint_names`, `body_pos_w`, `body_quat_w` in wxyz), `latency` (sample time to finished estimate, s), per-stream `age`, `model_reset`, `g1_segment_start` |
| `recording/motion-slim.csv.xz` (11/21) | the same per-frame timing and the live G1 arm targets (rad); the full 357 MB `motion.jsonl` of that session is not published |
| `recording/session.json` | configuration of the run: streams and placement, frame rate, gap and clock limits, model checkpoints, G1 joint and body names |
| `recording/calibration.json` | calibration result, including `tpose_variant` |
| `recording/sonic-live.json` | publisher to SONIC: delay, messages published, transmission pauses with start and end times |
| `real-controller*.json` | result of each controller session: watchdog triggered, stop acknowledged, reason |
| `real-controller-terminal*.log.xz` | console output of the official SONIC controller, including the frame index of every stream message it decoded |
| `o-sent.json` (11/21) | time the stop command `O` was sent after the app was closed |
| `probe-physical/summary.json` (11/21) | 20 Hz poll of the estimation server's status during the session |
| `studio*.log` | estimation server start-up lines |

Run 7 starts about 24 s before the robot received its first target and continues about 50 s after the stop. The web replay and Fig. 3 put time zero at the robot's first received target.

## Three-phone runs on 2026-11-22

From the field log kept on the laptop during the session. Times are KST.

| Run | Time | Code version | What happened | Published |
| --- | --- | --- | --- | --- |
| 1 | 16:56 | `b2a59f1` | followed per the operator; watchdog stop after the input of two iOS phones dropped | controller result |
| 2 | 17:29:45–17:33:58 | `3a0f56d` | 23 frames/s, p95 estimation latency 218 ms, 191 short transmission pauses; two browser windows of the web Studio were open on the laptop | controller result |
| 3–5 | 17:34–17:36 | `3a0f56d` | stop checks with the stop key, the emergency stop and closing the app (operator report) | – |
| 6 | 17:44:12–17:44:32 | `3a0f56d` | watchdog stop after about 20 s | controller result |
| 7 | 17:50:49–17:53:40 | `b2a59f1` | the run in the paper: both arms followed, 60.0 frames/s and 114 ms p95 in the Studio readout, watchdog stop after a 0.206 s frame gap | everything |

Code versions are commits of the team's private repository. The paper describes `b2a59f1`.

## What was cleaned

- Phone identifiers (`device_id`, `session_id`, `ar_reference_id` and the UUID inside `clock_id`) became pseudonyms named after the OS and the body position the phone streamed most, such as `ios-device-right-arm`. The same phone keeps the same pseudonym across both days. [`pseudonyms.json`](pseudonyms.json) lists them.
- Private IPv4 addresses became `<lan-ip-1>`, `<lan-ip-2>`; the laptop's home directory became `~`.
- Nothing else changed. Measurements, timestamps, estimates, controller output and the phone model strings are as recorded.

## License

CC BY 4.0, see [LICENSE.md](LICENSE.md). Please cite the paper when you use the data.
