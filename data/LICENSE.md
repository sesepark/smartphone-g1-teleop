# Licenses in this repository

| What | License |
| --- | --- |
| Code: `tools/`, `docs/index.html`, `docs/assets/replay.js`, `docs/assets/vendor/g1-mesh.js`, `data/launch-scripts/` | GPL-3.0 ([LICENSE](../LICENSE)) |
| Recorded data: `data/runs/`, `data/one-arm-replay/`, `data/pseudonyms.json`, the derived replay data in `docs/data/`, `figures/fig3_run7_timeline.json` | [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) |
| Paper and figure images: `paper/`, the images in `figures/`, `docs/assets/fig2_real_g1.jpg` | © 2026 the authors, all rights reserved |
| Documentation: README files, `EVIDENCE.md`, `THIRD_PARTY.md`, `AGENTS.md` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| G1 meshes: `docs/assets/vendor/g1-mesh-data.js` | BSD-3-Clause, Unitree Robotics ([notice](../docs/assets/vendor/UNITREE-LICENSE.txt)) |

Attribution for the data: Sanghyun An, Jae Wook Kang and Sehwan Park, "Hand-Held Smartphone Teleoperation of a G1 Humanoid Upper Body", KRoC 2027 (submitted), https://github.com/sesepark/smartphone-g1-teleop.

**Why non-commercial for the data.** The human poses in the logs are outputs of IMUCoCo, whose model was trained on motion data built on SMPL; the SMPL and AMASS licenses are non-commercial. Until that is clarified, the recorded data is shared for non-commercial use only.

**The paper and its figures** are shared for reading and review. For any other use, ask the authors. The conference's publication terms may apply after acceptance. Fig. 3 can be redrawn from the data with the code in `tools/`; the redrawn figure then falls under the data and code licenses, not under this reservation.
