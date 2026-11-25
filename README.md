# Hand-Held Smartphone Teleoperation of a G1 Humanoid Upper Body

**English** · [한국어](README.ko.md)

Humanoid teleoperation and demonstration collection usually need a VR headset or a motion-capture suit. We want ordinary smartphones to do that job. As a first step, three phones, one in each hand and one on the belt, teleoperated the upper body of a real Unitree G1 in real time.

**[Web replay of the robot run](https://sesepark.github.io/smartphone-g1-teleop/)** · **[Paper (PDF)](paper/KRoC2027_handheld_smartphone_G1_teleoperation.pdf)** · **[Experiment logs](data/README.md)** · **[Paper numbers and sources](EVIDENCE.md)**

- **What it is:** an undergraduate team research project at Seoul National University (Sanghyun An, Jae Wook Kang, Sehwan Park), submitted to KRoC 2027. This repository shares the paper, the logs of the robot runs, a browser replay and the scripts that check the paper's numbers. The system code stays in the team's private repository.
- **Built by the team:** phone collectors, multi-phone time sync and calibration, a live pipeline from phone IMUs to G1 joint targets, the connection to SONIC with an automatic stop, the Studio web interface, and an AR-based elbow method with an offline comparison.
- **Built on:** IMUCoCo (pose estimation from IMUs), NVIDIA SONIC (G1 whole-body policy), Unitree G1, ARKit and ARCore.

![Phone placement and the three-phone demonstration](figures/fig2_real_g1.jpg)

*(a) Phone placement seen from behind: iOS phones L and R in the hands, Android phone P on the belt. (b) The G1 on a gantry follows the operator. Paper Fig. 2; faces blurred.*

[![Web replay of the three-phone run on the real G1](figures/web-replay.jpg)](https://sesepark.github.io/smartphone-g1-teleop/)

*The [web replay](https://sesepark.github.io/smartphone-g1-teleop/) of the last three-phone run (2026-11-22): the human pose estimated from the phones, the G1 target pose sent to SONIC, and the timeline with the automatic stop. Both poses are what the estimation server recorded, not measurements of the robot.*

## Why smartphones

Phones already carry the sensors that wearable trackers use, an IMU and, on recent models, camera-based AR tracking, and most people own one. If a few phones could drive a humanoid, trying teleoperation or recording demonstrations would not start with buying dedicated gear. This project tests the first part of that idea on a real robot: can three hand-held or belt-worn phones drive a real G1 upper body in real time, stop it safely when input is lost, and can the phone's AR position fix what its IMU leaves ambiguous (the elbow)?

Demonstration data collection, policy learning and whole-body teleoperation are not part of this work yet.

## What we built on, and what we built

| Existing work we used | How we used it |
| --- | --- |
| [IMUCoCo](https://github.com/cmusmashlab/IMUCoCo) | Estimates a 24-joint human pose from IMUs at arbitrary body positions. We use the authors' public weights without retraining. |
| [NVIDIA SONIC](https://github.com/NVlabs/GR00T-WholeBodyControl) | G1 whole-body tracking policy and its official controller. It follows a short future window of joint references and keeps the robot balanced. |
| Unitree G1, ARKit, ARCore, Core Motion, Android sensors | Robot and phone platforms. |

Everything else in the pipeline was designed and implemented by the team. Each part answers a specific problem:

| Part | Problem | What the team did |
| --- | --- | --- |
| Phone collectors (iOS, Android) | Phones report rotation in different frames, and indoor magnetometer yaw is unreliable (one Android phone: 38.9° p95 disagreement with the gyro over 30 s) | Apps that stream magnetometer-free rotation (Android game rotation vector, iOS `xArbitraryZVertical`), linear acceleration and AR poses over UDP; about 50 IMU samples/s per iOS phone and 59/s for the Android phone in the robot run |
| Time sync and calibration | Three phones on three clocks and three yaw references | A four-timestamp clock exchange with the laptop once per second per phone; samples with offset uncertainty over 20 ms are dropped and the rest resampled to 60 Hz. An 8 s floor alignment and an 8 s palms-down T-pose map each phone into one body frame and onto its body segment |
| Live pose estimation | IMUCoCo is an offline model | A live loop on the laptop GPU that feeds calibrated phone data to IMUCoCo with the phones placed at the hands and behind the pelvis |
| G1 retargeting | Human and G1 limbs have different proportions and joint layouts | Bone-direction IK: match the direction of upper arm, forearm and hand rather than joint angles, by damped least squares on the arm joints only, with a 4 rad/s speed limit. When the IK error stays above 15° for 0.5 s, it re-solves from the home pose, a fix added during bring-up |
| SONIC connection | SONIC needs a steady stream of future references | Named 29-joint targets, delayed 0.35 s to fill SONIC's future window and sent at 50 Hz to the official controller, which commands the G1 over wired DDS |
| Automatic stop | A lost phone must not leave the robot following stale targets | An aligned-frame gap over 0.2 s resets the estimate and pauses transmission; a watchdog on the controller stops the robot after 0.5 s without references |
| Studio | Operators need to see calibration and tracking while the robot runs | A web interface that guides calibration and shows the estimated human pose next to the G1 targets with throughput and latency; the replay on this site reuses its G1 renderer |
| AR elbow (offline) | Hand-held IMUs cannot tell where the elbow is | The phone's AR wrist position and the estimated shoulder fix the elbow flexion (Eq. 3 in the paper); the swivel angle comes from the IMU estimate, and a blend handles AR dropouts. Compared with IMU-only by replaying recorded data |

The work is the team's joint effort; this repository does not divide it by person.

## What was verified on the real robot

The G1 hung from a gantry. One GPU laptop ran everything from phone reception to the SONIC controller.

| Demonstration | Phones | Result | Kind |
| --- | --- | --- | --- |
| 1st, 2026-11-21 | one iOS phone, right hand | the G1's right arm followed the operator's in three runs | observed on site and on video |
| | | app closed: **0.976 s** from the last received input to the watchdog's stop command | measured (logs) |
| 2nd, 2026-11-22 | iOS phones in both hands, Android phone on the belt | seven runs; both arms followed the operator's. The last run lasted about 2 min 50 s | observed on video; run times from the field log |
| | | last run: **60.0 frames/s** and **114 ms** p95 estimation latency for the 10 s window at 2 min 38 s, with the laptop's web window closed | computed by the estimation server during the run (field log) |
| | | ended when a 0.206 s frame gap on the laptop reset the estimate and the watchdog stopped the robot | measured (logs) |

How to read these numbers:

- 114 ms is the estimation latency, from the phone sample time to the finished pose estimate. It leaves out SONIC's 0.35 s reference delay and the robot's own response, so it is not the end-to-end teleoperation latency.
- Recomputed from the published log, the full 10 s windows from 0 to 160 s give 58.7–60.0 frames/s and 113.4–118.3 ms p95. In the last 8 s before the stop, throughput fell to 44.0 frames/s and p95 rose to 139 ms.
- The poses in the logs and the replay are the estimated human pose and the G1 joint targets sent to SONIC. The robot's joints were not logged, and following accuracy was not measured.

![Run on the real G1: arm elevation targets and estimation latency](figures/fig3_run7_timeline.png)

*Paper Fig. 3, the last run. (a) G1 arm elevation targets. (b) Estimation latency; dotted: automatic stop; gray: robot not following. `tools/fig3_run7_timeline.py` redraws it byte-identically from the published logs.*

**AR elbow, offline and preliminary.** Three one-arm development recordings (an Android phone in the left hand) were replayed through the same code with and without the AR hand position.

| Rec. | Condition | Elev. error (°) | Jerk p95, elbow / wrist (m/s³) |
| --- | --- | ---: | ---: |
| 1 | IMU-only | 25.85 | 517.7 / 903.1 |
| 1 | AR yaw | 25.88 | 520.8 / 905.6 |
| 1 | AR IK | 17.63 | 1617.9 / 3015.9 |
| 2 | IMU-only | 53.05 | 208.7 / 328.6 |
| 2 | AR IK | 56.01 | 255.3 / 431.5 |
| 2 (recomp.) | AR IK | 22.88 | 537.8 / 742.9 |
| 3 | IMU-only | 43.23 | 610.4 / 1028.5 |
| 3 | AR IK | 12.55 | 936.7 / 1461.8 |

The error fell in recordings 1 and 3. In recording 2 it rose with the AR input as recorded and fell only after that input was recomputed at the same timestamps. Wrist jerk rose 1.3–3.3×, above the 10% bound fixed in advance for a three-phone test. The AR method has not run on the robot.

## What we ran into

From the team's field logs of 2026-11-20 to 11-22, covering bring-up in simulation and the robot runs. Items marked *(logs)* can be checked in this repository.

- **Laptop load.** In simulation on 11/20, with the simulator viewer on the integrated GPU, the CPU throttled and estimates fell to 10–25 frames/s. Rendering moved to the NVIDIA GPU and inference to CUDA (7–9 ms). On 11/22, two Studio browser windows on the laptop again cut a run to 23 frames/s with a 218 ms p95.
- **Late samples.** A phone sample about 0.1 s late reset the estimate and paused output. The live settings now wait for late input and use a windowed clock filter with the 0.35 s reference delay.
- **IK drift.** Overhead motion pushed the warm-started IK into joint limits it did not recover from, which led to the re-solve rule above *(logs: `arm_escape` in session.json)*.
- **Robot mode.** The G1's high-level control was active and would have competed with SONIC; it was released once through the SDK while the robot was supported.
- **Wi-Fi.** A phone-hosted hotspot caused gaps of several seconds; a separate 5 GHz access point removed them, though shorter gaps remained.
- **The final stop.** In the last run, a 0.206 s frame gap reset the estimate; the phones' packets were still arriving, so the delay arose on the laptop *(logs)*.
- **No posture hold on stop.** The robot goes limp when it stops, so it must stay on the gantry.
- **Coupled arms.** In a three-phone input check, raising one arm moved the other arm's estimate by more than 15°, so the planned three-phone AR comparison was not recorded. The cause is not known yet.
- **AR jerk.** The AR elbow made the motion rougher (table above).

## Next steps

From the paper: run the AR elbow on the robot, design a filter that keeps its accuracy gain without the jerk, assign wrist twist to the G1 wrist separately in the IK, and run the three-phone comparison with added criteria. Input gaps from wireless reception and laptop processing also need work. Collecting demonstration data with phones, the motivation for all of this, comes after those steps.

## Levels of verification

| Level | What it covers | Where |
| --- | --- | --- |
| Recomputed from public logs | settings recorded with the runs, the robot window, the stop sequence, the 0.976 s stop, latency statistics, Fig. 3 | `python3 tools/check_paper_numbers.py` (35 checks) |
| Compared with a result table | Table 1 and the jerk ratios, against `metrics.csv`; the three source recordings are not public | same script |
| Observed, not logged | the robot following the operator | field video, not published (faces) |
| Not possible from this repository | independent reproduction of the system | needs the team's code, phones, a GPU laptop, a G1 and SONIC |

[EVIDENCE.md](EVIDENCE.md) lists every number in the paper with its kind (setting, measured, post-hoc, reported) and source.

## Getting started

```sh
git clone https://github.com/sesepark/smartphone-g1-teleop
cd smartphone-g1-teleop
python3 tools/check_paper_numbers.py                       # standard library only, about 10 s
python3 -m http.server 8000 --directory docs               # local copy of the replay at http://127.0.0.1:8000
```

To rebuild derived files: `python3 tools/build_web_replay.py data/runs/20261122-174632-live-three-phone-dev docs/data` and `uv run --no-project --with numpy --with matplotlib python tools/fig3_run7_timeline.py`. `tools/prepare_public_data.py` records how the public logs were made from the team's raw archive.

## Documents

| Document | Contents |
| --- | --- |
| [paper/](paper/README.md) | the manuscript (PDF, Korean with an English abstract) |
| [EVIDENCE.md](EVIDENCE.md) | every number and setting in the paper, its kind and its source |
| [data/README.md](data/README.md) | file formats, the run list of 2026-11-22, what was anonymized |
| [data/one-arm-replay/README.md](data/one-arm-replay/README.md) | conditions and columns behind Table 1 |
| [THIRD_PARTY.md](THIRD_PARTY.md) | G1 meshes, IMUCoCo, SMPL and SONIC |

## Scope

- Real-robot results are from a gantry-supported G1 over two days of runs. The AR elbow results are from three development recordings.
- Not included: the system code, the three one-arm source recordings, the recordings behind 38.9° and τ = 4.66 s, and videos with faces.
- Phone identifiers, the laptop's LAN address and home paths were replaced; measurements and timestamps are unchanged.

## Citation

```bibtex
@inproceedings{an2027smartphone,
  title     = {Hand-Held Smartphone Teleoperation of a {G1} Humanoid Upper Body},
  author    = {An, Sanghyun and Kang, Jae Wook and Park, Sehwan},
  booktitle = {Korea Robotics Society Annual Conference (KRoC)},
  year      = {2027},
  note      = {Submitted}
}
```

## License

Code is GPL-3.0 ([LICENSE](LICENSE)). The logs in `data/` and `docs/data/` are CC BY-NC 4.0, because the human poses come from a model trained on SMPL/AMASS-based data under non-commercial terms. The paper and its figures remain © the authors, shared for reading and review; for other uses, ask the authors. The G1 meshes keep Unitree's BSD-3-Clause license. Full table: [data/LICENSE.md](data/LICENSE.md).
