# Third-party components

| Component | Where it appears | Source | License |
| --- | --- | --- | --- |
| Unitree G1 visual meshes (simplified) | `docs/assets/vendor/g1-mesh-data.js` | [unitree_mujoco](https://github.com/unitreerobotics/unitree_mujoco) `unitree_robots/g1/meshes`, commit `1eb6642e3f3fdfb7fb13a9794fd6a2dd93ea0e7d`; triangle-simplified, body-local vertices, rubber hands excluded | BSD-3-Clause, [notice](docs/assets/vendor/UNITREE-LICENSE.txt) |
| G1 WebGL renderer | `docs/assets/vendor/g1-mesh.js` | the team's estimation-server viewer (private repository) | GPL-3.0, same as this repository |
| IMUCoCo | named in the logs (`session.json`), not bundled | [cmusmashlab/IMUCoCo](https://github.com/cmusmashlab/IMUCoCo), commit `d7dd17c`, with the authors' public checkpoints | GPL-3.0; checkpoints under the authors' terms |
| GEAR-SONIC / GR00T Whole-Body Control | controller output in `real-controller-terminal*.log.xz`, not bundled | [NVlabs/GR00T-WholeBodyControl](https://github.com/NVlabs/GR00T-WholeBodyControl) | upstream code and model licenses |

No endorsement by Unitree, NVIDIA, Apple or Google is implied.
