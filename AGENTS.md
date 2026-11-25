# Repository instructions

## What this repository is

- Public companion to the KRoC 2027 paper "Hand-Held Smartphone Teleoperation of a G1 Humanoid Upper Body" (An, Kang, Park). It holds logs, figures, the web replay in `docs/` (GitHub Pages) and the scripts that recompute the paper's numbers.
- The submitted manuscript is final. Do not edit the paper or change numbers here to differ from it. If a log disagrees with the paper, report it; do not "fix" either side silently.
- `paper/` holds the manuscript PDF as sent to the team on 2026-11-25 (final text plus one repository sentence at the end of Sec. 6). Replace it only with a version the authors sent; keep it and the figures out of the CC BY license.
- The system code (phone apps, estimation server, SONIC bridge) lives in the team's private repository. Do not copy it here without the team's agreement.

## Data rules

- Keep measured, setting, post-hoc and reported values apart, as in `EVIDENCE.md`. Estimated poses and G1 targets are not robot measurements.
- Public data must not contain phone identifiers, private IP addresses, home paths, emails or unblurred faces. New logs go through `tools/prepare_public_data.py` or the same rules, then a scan for UUIDs, IPs and paths.
- After changing data, regenerate `data/SHA256SUMS` and run `python3 tools/check_paper_numbers.py`; all checks must pass.
- Keep files under 50 MB; compress logs with xz.

## README 작성 기준

- 개인 소개는 [Hoyun Kim](https://github.com/kimhoyun-robotair), 프로젝트는 [Pavan](https://github.com/Pavankv92/Portfolio#readme)과 [Biped Walking Controller](https://github.com/rdesarz/biped-walking-controller#readme)의 구성 원칙을 따른다.
- 프로젝트 README 순서: 프로젝트명·소개 → 성격·주요 작업·기술 → 실제 대표 자료 → 프로젝트 개요 → 구현 내용 → 필요한 결과·검증 → 시작하기 → 문서 → 사용 범위와 한계 → 관련 프로젝트. 해당하지 않는 절은 생략한다.
- 서비스는 실제 화면·사용 흐름, 로봇·실험은 장비·입출력·검증 결과, CLI는 실제 사용 예제를 중점으로 쓴다. 팀 프로젝트는 본인과 팀·원본의 기여를 구분한다.
- 자연스러운 한국어를 사용하고 반복되는 어미·과도한 강조·커밋 수 나열을 피한다. 수치에는 시점·조건을 적고 실물·시뮬레이션·미검증을 구분한다.
- 기존 이미지를 우선 활용하고 빈 화면·연결 전 상태를 밝힌다. 상세 설명은 링크된 문서로 보존한다. 링크·이미지 경로와 실제 렌더링을 확인한다.
- 새 개인 저장소에도 이 지침을 전달한다. 기존 AGENTS.md의 작업·안전 규칙을 보존하며 팀 저장소·보관 저장소의 변경 제한을 우선 확인한다.
- 작업공간에 `readme-standard`가 있으면 그 저장소의 README·템플릿·유형별 안내를 먼저 읽는다. 사용자 최신 지시가 이 기준보다 우선한다.
