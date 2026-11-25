#!/usr/bin/env python3
"""Recompute the paper's numbers from the published logs.

    python3 tools/check_paper_numbers.py           # prints a report, exits 1 if a check fails
    python3 tools/check_paper_numbers.py --json    # machine-readable result

Standard library only. Each check names the paper section it supports. "post-hoc" marks
numbers computed after the experiment from the same logs; they are not quoted in the paper
unless the check says so.
"""
import csv
import json
import lzma
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN7 = ROOT / 'data/runs/20261122-174632-live-three-phone-dev'
RUN1121 = ROOT / 'data/runs/20261121-215716-g1-supported-one-iphone'
SCRIPTS = ROOT / 'data/launch-scripts'
METRICS = ROOT / 'data/one-arm-replay/metrics.csv'
PUBLISH_HZ, WATCHDOG_S = 50.0, 0.5

results = []


def check(section, claim, value, ok, note=''):
    results.append(dict(section=section, claim=claim, value=value, ok=bool(ok), note=note))


def text(path):
    path = Path(path)
    return path.read_text(errors='replace') if path.exists() else lzma.open(str(path) + '.xz', 'rt', errors='replace').read()


def lines(path):
    path = Path(path)
    return path.open() if path.exists() else lzma.open(str(path) + '.xz', 'rt')


def pct(values, q):
    v = sorted(values)
    k = (len(v) - 1) * q / 100
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def near(a, b, tol):
    return abs(a - b) <= tol


def run7():
    rec = RUN7 / 'recording'
    session = json.loads((rec / 'session.json').read_text())
    sonic = json.loads((rec / 'sonic-live.json').read_text())
    ctl = json.loads((RUN7 / 'real-controller-run7.json').read_text())
    calib = json.loads((rec / 'calibration.json').read_text())
    cfg = session['config']

    # 3.1 / 3.2 settings recorded with the run
    check('3.1', 'Resampled to 60 Hz; samples whose clock-offset uncertainty exceeds 20 ms rejected',
          f"fps={cfg['fps']}, max_clock_uncertainty={cfg['max_clock_uncertainty']} s",
          cfg['fps'] == 60 and cfg['max_clock_uncertainty'] == 0.02)
    check('3.1', 'T-pose held palms down', calib.get('tpose_variant'), calib.get('tpose_variant') == 'palms_down')
    pel = cfg['streams']['pelvis']
    check('3.2', 'Hand phones at the hands, belt phone behind the pelvis',
          f"left_arm joint {cfg['streams']['left_arm']['joint']}, right_arm joint {cfg['streams']['right_arm']['joint']}, "
          f"pelvis joint {pel['joint']} at {pel['position']}",
          cfg['streams']['left_arm']['joint'] == 20 and cfg['streams']['right_arm']['joint'] == 21 and pel['position'][2] < 0)
    check('3.2', 'Only the arm joints are updated', cfg['g1_target_scope'], cfg['g1_target_scope'] == 'arms')
    check('3.2', 'Joint speed limited to 4 rad/s', f"max_joint_speed_rad_s={session['robot']['max_joint_speed_rad_s']}",
          session['robot']['max_joint_speed_rad_s'] == 4.0)
    check('3.2', 'Reference delayed 0.35 s for SONIC', f"delay_seconds={sonic['delay_seconds']}", sonic['delay_seconds'] == 0.35)
    check('3.2', 'Frame gap over 0.2 s resets the estimate', f"max_gap_seconds={cfg['max_gap_seconds']}",
          cfg['max_gap_seconds'] == 0.2)
    check('3.2', 'Watchdog stops the robot after 0.5 s without input',
          f"watchdog_timeout_seconds={ctl['watchdog_timeout_seconds']}", ctl['watchdog_timeout_seconds'] == 0.5)
    # SHA-256 of the IMUCoCo authors' public checkpoint files (synergylabs.org/haozhe/*.pth), as downloaded by the team.
    public = {'imucoco_best': 'a560a41324cff005c3cec88bf7b579de9cecd18fe3e67eae7def70cf6d60fb13',
              'all_error_loss_map': 'a6b25986f4232d1dba5e815eb8537cc8e501eff3ea9dacd5d26c7867d828cf30',
              'poser_dtp_best': '9bf8412c0cd1d5e938530d9d92503c6ae9b5c86c592f34ba57edaa4c96068629'}
    check('3.2', 'Weights: the IMUCoCo authors\' public checkpoints, unchanged, loaded without missing keys',
          f"backend={session['model']['backend']}, upstream {session['model']['upstream_commit'][:7]}, "
          f"checkpoint hashes match: {session['model']['checkpoints'] == public}",
          session['model']['backend'] == 'imucoco' and session['model']['checkpoints'] == public
          and session['model']['checkpoint_load'][0]['missing'] == [])

    # Robot window from the controller log (same mapping as Fig. 3)
    log = text(RUN7 / 'real-controller-terminal-run7.log').replace('\r', '\n')
    idx = [int(x) for x in re.findall(r'Frame\[0\] \(idx=(\d+)\)', log)]
    decode = [int(x) for x in re.findall(r'Decode interval: (\d+) ms', log)]
    consecutive = idx == list(range(idx[0], idx[-1] + 1))
    check('4.2', 'Controller decoded consecutive stream frames, no index skipped',
          f'{len(idx)} frames, index {idx[0]}-{idx[-1]}', consecutive and len(idx) == 8377)
    check('4.2', 'Controller receive span and mean interval',
          f'{sum(decode) / 1e3:.1f} s, mean {sum(decode) / len(decode):.2f} ms',
          near(sum(decode) / 1e3, 168.3, 0.05) and near(sum(decode) / len(decode), 20.09, 0.01),
          'Fig. 3 notes: 168.3 s and 20.09 ms')
    pauses = sorted((p['start_monotonic'], p['end_monotonic']) for p in sonic['recent_pauses'])
    first = sonic['last_send_monotonic'] - sonic['published'] / PUBLISH_HZ - sum(e - s for s, e in pauses)

    def at(k):
        t, remaining = first, k / PUBLISH_HZ
        for s, e in pauses:
            if t + remaining <= s:
                break
            remaining -= s - t
            t = e
        return t + remaining
    t_on, t_last = at(idx[0]), at(idx[-1])
    long = max(sonic['recent_pauses'], key=lambda p: p['seconds'])
    t_stop = long['start_monotonic'] + WATCHDOG_S
    check('Fig. 3', 'Robot window: controller frame indices mapped onto the 50 Hz send timeline (post-hoc)',
          f'{t_last - t_on:.1f} s', near(t_last - t_on, 168.0, 0.05))
    check('4.2', 'Last message to the robot sits just before the long pause',
          f"{long['start_monotonic'] - t_last:.3f} s before a {long['seconds']:.3f} s pause",
          0 <= long['start_monotonic'] - t_last < 0.2 and long['seconds'] > WATCHDOG_S)
    inside = [p for p in sonic['recent_pauses'] if t_on <= p['start_monotonic'] < long['start_monotonic']]
    check('4.2', 'Earlier pauses inside the robot window stayed under the watchdog',
          f"{len(inside)} pauses, longest {max(p['seconds'] for p in inside):.3f} s",
          len(inside) == 6 and max(p['seconds'] for p in inside) < WATCHDOG_S)
    check('4.2', 'Controller reports the watchdog stop',
          f"watchdog_triggered={ctl['watchdog_triggered']}, reason={ctl['reason']!r}",
          ctl['watchdog_triggered'] and ctl['stop_acknowledged'])

    # Per-frame estimates
    ts, lat, resets = [], [], []
    for line in lines(rec / 'motion.jsonl'):
        d = json.loads(line)
        ts.append(d['t'])
        lat.append(d.get('latency'))
        if d.get('model_reset'):
            resets.append(d['t'])
    gaps = [(a, b - a) for a, b in zip(ts, ts[1:]) if t_on < b <= t_stop + 1 and b - a > 0.2]
    check('4.2', 'Frame interval over 0.2 s just before the stop, estimate reset',
          ', '.join(f'{g:.3f} s at {a - t_on:.2f} s' for a, g in gaps),
          len(gaps) == 1 and near(gaps[0][1], 0.206, 0.0005) and any(abs(r - sum(gaps[0])) < 1e-6 for r in resets))
    win = [l * 1e3 for t, l in zip(ts, lat) if t_on <= t <= t_last and l is not None]
    check('Fig. 3', 'Estimation latency inside the robot window (post-hoc)',
          f'p50 {pct(win, 50):.1f} ms, p95 {pct(win, 95):.1f} ms',
          near(pct(win, 50), 111.8, 0.05) and near(pct(win, 95), 115.2, 0.05), 'not quoted in the paper text')
    fps, p95 = [], []
    start = 0.0
    while start + 10 <= t_last - t_on:
        w = [l * 1e3 for t, l in zip(ts, lat) if start <= t - t_on < start + 10 and l is not None]
        fps.append(len(w) / 10)
        p95.append(pct(w, 95))
        start += 10
    tail = [l * 1e3 for t, l in zip(ts, lat) if start <= t - t_on < t_last - t_on and l is not None]
    tail_fps = len(tail) / (t_last - t_on - start)
    check('4.2', 'Consistency with the 60.0 frames/s and 114 ms p95 read during the run (10 s window at 2 min 38 s)',
          f'{len(fps)} full 10 s windows, 0-{start:.0f} s: {min(fps):.1f}-{max(fps):.1f} frames/s, p95 {min(p95):.1f}-{max(p95):.1f} ms; '
          f'last {t_last - t_on - start:.0f} s before the stop: {tail_fps:.1f} frames/s, p95 {pct(tail, 95):.1f} ms',
          min(fps) >= 58 and max(fps) <= 60.05 and min(p95) <= 114 <= max(p95),
          'post-hoc. The paper value was read from the estimation server during the run and is not in the logs; '
          'this only shows that it is typical of the robot window before the final seconds')

    # Raw packets: three phones, AR received and logged only
    counts, last_rx, near_stop = {}, {}, {}
    gap_at = gaps[0][0] if gaps else t_stop
    for line in lines(rec / 'raw.jsonl'):
        d = json.loads(line)
        p = d['packet']
        key = (p.get('stream_id'), p.get('type'))
        counts[key] = counts.get(key, 0) + 1
        if p.get('type') == 'ar_pose' and t_on <= d['receive_time'] <= t_last:
            counts[(key, 'robot')] = counts.get((key, 'robot'), 0) + 1
        if p.get('type') == 'sample':
            s, t = p['stream_id'], d['receive_time']
            if s in last_rx and gap_at - 0.5 <= t <= gap_at + 0.5:
                near_stop[s] = max(near_stop.get(s, 0.0), t - last_rx[s])
            last_rx[s] = t
    streams = sorted({s for s, kind in counts if kind == 'sample'})
    check('4.1', 'Three phones streamed IMU samples', ', '.join(streams), streams == ['left_arm', 'pelvis', 'right_arm'])
    ar = {s: counts.get(((s, 'ar_pose'), 'robot'), 0) / (t_last - t_on) for s in streams}
    check('6', 'AR poses were received and logged during the robot window (about 60/s iOS, 30/s Android)',
          ', '.join(f'{s} {v:.0f}/s' for s, v in ar.items()),
          ar['left_arm'] > 50 and ar['right_arm'] > 50 and 20 < ar['pelvis'] < 40)
    script = (SCRIPTS / 'real-1122/1-studio-live-3phone.sh').read_text()
    check('6', 'AR coupling was off on the robot (no AR flag in the launch script)',
          'flags: ' + ' '.join(sorted(set(re.findall(r'--[a-z-]+', script)))),
          '--three-phone-ar' not in script and '--one-phone-ar' not in script)
    check('4.2', 'Phone packets kept arriving around the 0.206 s frame gap (post-hoc)',
          'largest receive gap within 0.5 s of it: ' + ', '.join(f'{s} {g * 1e3:.0f} ms' for s, g in sorted(near_stop.items())),
          len(near_stop) == 3 and max(near_stop.values()) < 0.1,
          'so the frame gap arose on the laptop after reception; the paper attributes the stop to laptop processing and communication delay')


def run1121():
    o = json.loads((RUN1121 / 'o-sent.json').read_text())['o_sent_monotonic']
    ctl = json.loads((RUN1121 / 'real-controller-run1.json').read_text())
    last = None
    for line in lines(RUN1121 / 'recording/raw.jsonl'):
        d = json.loads(line)
        if d['packet'].get('type') == 'sample' and d['receive_time'] <= o:
            last = d['receive_time']
    check('4.2', '1st demonstration: stop command sent 0.976 s after the last received input when the app was closed',
          f'{o - last:.3f} s (last sample received -> O sent)', near(o - last, 0.976, 0.0005))
    check('4.2', '1st demonstration: the stop came from the watchdog',
          f"watchdog_triggered={ctl['watchdog_triggered']}, reason={ctl['reason']!r}", ctl['watchdog_triggered'])
    spans = []
    for name in ('real-controller-terminal-run1.log', 'real-controller-terminal-run2.log', 'real-controller-terminal.log'):
        idx = [int(x) for x in re.findall(r'Frame\[0\] \(idx=(\d+)\)', text(RUN1121 / name))]
        spans.append((name, idx[0], idx[-1]) if idx else (name, None, None))
    distinct = all(a is not None for _, a, _ in spans) and len({(a, b) for _, a, b in spans}) == 3
    check('4.2', '1st demonstration: three controller sessions received stream frames',
          ', '.join(f'{n.replace("real-controller-terminal", "terminal")}: idx {a}-{b}' for n, a, b in spans), distinct,
          'distinct frame ranges per session; following itself was observed by the operator and on video, not logged')
    session = json.loads((RUN1121 / 'recording/session.json').read_text())
    streams = sorted(session['config']['streams'])
    check('4.1', '1st demonstration: one phone in the right hand', ', '.join(streams), streams == ['right_arm'])


def table1():
    rows = list(csv.DictReader(METRICS.open()))
    get = lambda c, v: next(r for r in rows if r['case'] == c and r['variant'] == v)
    paper = [('1', 'IMU-only', 'd', 'imu-only', 25.85, 517.7, 903.1), ('1', 'AR yaw', 'd', 'default', 25.88, 520.8, 905.6),
             ('1', 'AR IK', 'd', 'ar-ik', 17.63, 1617.9, 3015.9), ('2', 'IMU-only', 'f-original', 'imu-only', 53.05, 208.7, 328.6),
             ('2', 'AR IK', 'f-original', 'ar-ik', 56.01, 255.3, 431.5), ('2 (recomp.)', 'AR IK', 'f', 'ar-ik', 22.88, 537.8, 742.9),
             ('3', 'IMU-only', 'g', 'imu-only', 43.23, 610.4, 1028.5), ('3', 'AR IK', 'g', 'ar-ik', 12.55, 936.7, 1461.8)]
    for rec, cond, case, var, el, je, jw in paper:
        r = get(case, var)
        got = (round(float(r['nominal_elevation_mae_deg']), 2), round(float(r['elbow_jerk_p95_m_s3']), 1),
               round(float(r['wrist_jerk_p95_m_s3']), 1))
        check('Table 1', f'Rec. {rec}, {cond}', f'{got[0]:.2f}°, {got[1]:.1f} / {got[2]:.1f} m/s³', got == (el, je, jw))
    ratio = lambda c, col: float(get(c, 'ar-ik')[col]) / float(get(c, 'imu-only')[col])
    wrist = [ratio(c, 'wrist_jerk_p95_m_s3') for c in ('d', 'f-original', 'f', 'g')]
    elbow = [ratio(c, 'elbow_jerk_p95_m_s3') for c in ('d', 'f-original', 'f', 'g')]
    check('5.3', 'Jerk p95 rose 1.3-3.3x at the wrist, 1.2-3.1x at the elbow',
          f'wrist {min(wrist):.2f}-{max(wrist):.2f}x, elbow {min(elbow):.2f}-{max(elbow):.2f}x',
          f'{min(wrist):.1f}-{max(wrist):.1f}' == '1.3-3.3' and f'{min(elbow):.1f}-{max(elbow):.1f}' == '1.2-3.1')


def main():
    for part in (run7, run1121, table1):
        try:
            part()
        except FileNotFoundError as e:
            check(part.__name__, 'input files present', str(e), False)
    if '--json' in sys.argv:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"[{'ok' if r['ok'] else 'FAIL'}] {r['section']:<8} {r['claim']}\n         {r['value']}"
                  + (f"\n         ({r['note']})" if r['note'] else ''))
        print(f"\n{sum(r['ok'] for r in results)}/{len(results)} checks passed")
    sys.exit(0 if all(r['ok'] for r in results) else 1)


if __name__ == '__main__':
    main()
