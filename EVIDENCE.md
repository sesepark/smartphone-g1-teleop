# Paper numbers and their sources

Each statement in the paper, where its value comes from, and whether this repository can check it. `check` means `python3 tools/check_paper_numbers.py` recomputes or reads it from the published files. Section numbers follow the submitted paper.

Kinds: **measured** (logged during an experiment), **setting** (a parameter recorded with the run), **post-hoc** (computed afterwards from the same logs), **reported** (observed by the operator or on video, or written in the field log, but not in the published logs).

## 3. Real-time pipeline

| Paper statement | Value | Kind | Source | In this repo |
| --- | --- | --- | --- | --- |
| Magnetometer yaw vs gyro integration on one Android phone, p95 over 30 s windows | 38.9° | measured | development recording and audit script in the team repository | not included |
| Phone rotation without the magnetometer (Android game rotation vector, iOS `xArbitraryZVertical`) | – | setting | phone apps (team repository); raw packets are in sensor-to-world quaternions | packets in `raw.jsonl.xz` |
| Four-timestamp clock sync; samples whose clock-offset uncertainty exceeds 20 ms rejected | 20 ms | setting | run 7 `session.json` `max_clock_uncertainty`; `sync_result` packets (t0–t3, once per second per phone) in `raw.jsonl.xz` | check |
| Resampled to 60 Hz | 60 Hz | setting | run 7 `session.json` `fps` | check |
| Floor alignment, then palms-down T-pose, 8 s each | palms down | setting | run 7 `calibration.json`; `calibration_event` packets | check (pose variant) |
| IMUCoCo public weights, no retraining | upstream `d7dd17c` | setting | run 7 `session.json` `model`: checkpoint SHA-256 equal to the authors' public files, no missing keys | check |
| Hand phones at the hands, belt phone behind the pelvis | joints 20, 21, 0 | setting | run 7 `session.json` `streams` | check |
| Direction IK updates the arm joints only, joint speed limit 4 rad/s | arms, 4 rad/s | setting | run 7 `session.json` `g1_target_scope`, `robot.max_joint_speed_rad_s` | check |
| Damped least squares, λ | 0.008 | setting | retargeting code (team repository) | not included |
| IK re-solve from home when the error stays above 15° for 0.5 s (not in the paper; added during bring-up) | 15°, 0.5 s | setting | run 7 `session.json` `robot.arm_escape` | file |
| SONIC reference delayed 0.35 s and sent at 50 Hz | 0.35 s, 50 Hz | setting, measured | run 7 `sonic-live.json`; controller mean receive interval 20.09 ms | check |
| Frame gap over 0.2 s resets the estimate; 0.5 s without transmission stops the robot | 0.2 s, 0.5 s | setting | run 7 `session.json` `max_gap_seconds`, `real-controller-run7.json` | check |

## 4. Real-robot demonstration

| Paper statement | Value | Kind | Source | In this repo |
| --- | --- | --- | --- | --- |
| One GPU laptop from phone reception to the SONIC controller; wired DDS to the G1 | – | setting | `data/launch-scripts/` (`--model-device cuda`, `--interface enp4s0`) | files |
| 1st demonstration: one iOS phone in the right hand | – | setting | 11/21 `session.json` streams | check |
| 1st demonstration: the right arm followed in three runs | 3 | reported | operator and field log; the three controller sessions received stream frames (distinct frame ranges in the three terminal logs) | check (sessions) |
| 1st demonstration: stop 0.976 s after the last input when the app was closed | 0.976 s | measured | last received sample in 11/21 `raw.jsonl.xz` to the stop command `O` in `o-sent.json` (0.01 s resolution); the app-closure moment itself is not logged | check |
| 2nd demonstration: two iOS phones in the hands, one Android phone on the belt | – | setting | run 7 `raw.jsonl.xz` streams and clock ids | check (streams) |
| Seven runs with three phones | 7 | measured, reported | [data/README.md](data/README.md#three-phone-runs-on-2026-11-22) run list; controller results of runs 1, 2, 6, 7 | partly (run 7 full) |
| Earlier runs stopped early or ran slower; one at 23 frames/s | 23 frames/s | reported | run 2 value in the field log | not included |
| Last run lasted about 2 min 50 s | 17:50:49 to 17:53:40 KST | reported | field log (streaming start to stop); the controller log shows frames received over 168.3 s | check (168.3 s) |
| 60.0 frames/s, p95 estimation latency 114 ms over the 10 s window at 2 min 38 s, web window closed | 60.0, 114 ms | reported | computed by the estimation server during the run and written in the field log; not in the published logs | post-hoc consistency check: full 10 s windows 0–160 s give 58.7–60.0 frames/s and 113.4–118.3 ms; the last 8 s give 44.0 frames/s and 139 ms |
| Estimation latency steady while following, a few spikes (Fig. 3b) | p50 111.8, p95 115.2 ms | post-hoc | run 7 `motion.jsonl.xz` `latency` within the robot window | check |
| Stop: laptop processing and communication delay pushed the frame interval over 0.2 s; the watchdog stopped the robot | 0.206 s gap, 0.745 s pause | measured, post-hoc | run 7 `motion.jsonl.xz` (gap at 168.04 s and `model_reset`), `sonic-live.json` (pause 168.06–168.81 s), controller result (watchdog). Within 0.5 s of the gap no phone's packets paused for more than 44 ms, so the gap arose on the laptop. The stop time (≈168.56 s) is inferred as pause start + 0.5 s; the controller log has no timestamp for it | check |
| Robot window on the time axis of Fig. 3 | 168.0 s | post-hoc | controller frame indices mapped onto the 50 Hz publisher timeline (the controller's own receive span is 168.3 s) | check |

## 5. Elbow from the AR hand position

| Paper statement | Value | Kind | Source | In this repo |
| --- | --- | --- | --- | --- |
| Three one-arm development recordings, Android phone in the left hand | 3 | – | source recordings (team storage) | metrics only |
| Table 1, all eight rows | see table | post-hoc | `data/one-arm-replay/metrics.csv` | check |
| Wrist jerk p95 up 1.3–3.3×, elbow 1.2–3.1× | ratios | post-hoc | `metrics.csv` | check |
| Time constant τ from static IMU yaw drift and AR yaw noise | 4.66 s | setting derived from measurements | static recording (team storage) | not included |
| Criteria fixed in advance (yaw drift down ≥ 30% in two of three phones, jerk increase ≤ 10%) | – | setting | trial protocol written before the test (team repository) | not included |
| In the input check, the other arm moved over 15° when one arm was raised | > 15° | measured | three-phone trial of 2026-11-22, ended 18:13 (not published) | not included |

## 6. Conclusion and limitations

| Paper statement | Value | Kind | Source | In this repo |
| --- | --- | --- | --- | --- |
| AR coupling not on the robot path; AR poses of the three phones were received and logged only | about 60/s per iOS phone, 30/s Android | measured, setting | run 7 `raw.jsonl.xz` `ar_pose` packets; launch script without `--three-phone-ar` | check |
| The robot goes limp when it stops, so a gantry is needed | – | reported | field log of 2026-11-21 | not included |

## Figures

| Figure | File | Made from |
| --- | --- | --- |
| Fig. 1 System overview | [figures/fig1_system.png](figures/fig1_system.png) (source [SVG](figures/fig1_system.svg)) | drawn by hand; settings only, no measurements |
| Fig. 2 Phone placement and demonstration | [figures/fig2_real_g1.jpg](figures/fig2_real_g1.jpg) | (a) 3D render, (b) frame from the field video, faces blurred |
| Fig. 3 Run on the real G1 | [figures/fig3_run7_timeline.png](figures/fig3_run7_timeline.png), [summary](figures/fig3_run7_timeline.json) | `tools/fig3_run7_timeline.py` on run 7 |
| Fig. 4 Elbow from the AR hand position | [figures/fig4_swivel.png](figures/fig4_swivel.png) | drawn for illustration; lengths and angles are not measurements |

The four figure files are identical to the images embedded in the submitted manuscript (checked by SHA-256 on 2026-11-25).
