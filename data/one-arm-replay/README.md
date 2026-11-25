# One-arm AR replay (Table 1)

`metrics.csv` holds the metrics behind Table 1 of the paper. Three one-arm development recordings, made with one Android phone held in the left hand, were replayed offline through the same code (team commit `7416ccc1`) under each condition. The source recordings are not in this repository.

## Recordings and conditions

| Paper | `case` | Recording |
| --- | --- | --- |
| 1 | `d` | development recording D |
| 2 | `f-original` | recording F with the AR input as recorded (AR recovery was rejected during recording, so the AR input reached only part of the run) |
| 2 (recomp.) | `f` | recording F with the AR input recomputed at the same 2,436 timestamps |
| 3 | `g` | development recording G |

| Paper | `variant` | `mode` | Meaning |
| --- | --- | --- | --- |
| IMU-only | `imu-only` | `imu_only` | phone IMU only |
| AR yaw | `default` (case `d`) | `archived_ar_yaw` | IMU plus the yaw correction from AR stored with recording D |
| AR IK | `ar-ik` | `swivel_blend` | IMU plus the AR hand position through the swivel IK and blend (Eq. 3) |

For `f-original`, `f` and `g` the `default` row equals `ar-ik`, because those recordings already used the swivel blend.

## Columns

| Column | Meaning |
| --- | --- |
| `frames` | aligned pose frames in the replay |
| `nominal_frames`, `nominal_elevation_mae_deg` | frames inside pose intervals fixed beforehand from the video, and the mean absolute error between the estimated shoulder-to-wrist elevation and the nominal angle (0°, ±90°). Recording 1: five intervals (T-pose, arm down, arms up); recordings 2 and 3: one 3 s arms-up interval each. The replay keeps only aligned pose frames, and their rate differs between recordings: the 3 s interval holds 54 frames in recording 2 (about 18/s) and 110 in recording 3 (about 37/s). The source report does not explain the difference |
| `elbow_bend_mean_deg`, `elbow_bend_p95_deg` | elbow flexion of the estimated human pose, 0° = straight |
| `elbow_jerk_p95_m_s3`, `wrist_jerk_p95_m_s3` | p95 of the joint position jerk over the whole recording, third finite difference on the real timestamps, windows across a reset excluded |
| `jerk_windows` | jerk windows used |
| `admitted_position_ik_frames`, `positive_blend_weight_frames` | frames where the AR position IK was accepted / had a positive blend weight |
| `camera_tracked`, `anchor_tracked`, `camera_and_anchor_tracked`, `ar_packets`, `camera_tracking_pct`, `camera_and_anchor_pct` | AR tracking state of the received AR packets |

All metrics describe the estimated human pose. None of them is a robot measurement or an independent ground truth, and the elevation error is an auxiliary metric: it was not one of the criteria fixed in advance for the three-phone test.

`python3 tools/check_paper_numbers.py` rounds these values and compares them with every cell of Table 1.
