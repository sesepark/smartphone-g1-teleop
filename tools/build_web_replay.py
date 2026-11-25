#!/usr/bin/env python3
"""Pack the three-phone run on the real G1 (run 7, 2026-11-22) for the web replay.

Reads the public run folder (motion.jsonl[.xz], sonic-live.json, controller log) and writes
docs/data/run7.bin (int16 poses) and docs/data/run7.json (metadata, timeline, events).
Standard library only.

    python3 tools/build_web_replay.py data/runs/20261122-174632-live-three-phone-dev docs/data

The human pose is the IMUCoCo estimate; the G1 pose is the joint target sent to SONIC,
both as recorded by the estimation server. Neither is a measurement of the robot.
"""
import array
import json
import lzma
import math
import re
import sys
from pathlib import Path

PUBLISH_HZ = 50.0   # sonic_live.py publishes the pose topic at 50 Hz
WATCHDOG_S = 0.5    # real-controller-run7.json watchdog_timeout_seconds
STEP = 2            # keep every 2nd frame of the 60 Hz estimate -> 30 fps replay
SHOULDER, WRIST = {'left': 16, 'right': 23}, {'left': 20, 'right': 27}   # body indices (pitch link, wrist roll link)


def open_text(path):
    path = Path(path)
    if path.exists():
        return path.open()
    return lzma.open(str(path) + '.xz', 'rt')


def index_to_time(sonic):
    """Map a publisher message index to Studio time (same rule as the paper's Fig. 3 script)."""
    pauses = sorted((p['start_monotonic'], p['end_monotonic']) for p in sonic['recent_pauses'])
    assert len(pauses) == sonic['pause_count'], 'pause list is truncated'
    first = sonic['last_send_monotonic'] - sonic['published'] / PUBLISH_HZ - sum(e - s for s, e in pauses)

    def at(k):
        t, remaining = first, k / PUBLISH_HZ
        for s, e in pauses:
            if t + remaining <= s:
                break
            remaining -= s - t
            t = e
        return t + remaining
    return at


def percentile(values, q):
    v = sorted(values)
    k = (len(v) - 1) * q / 100
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def elevation(body, side):
    s, w = body[SHOULDER[side]], body[WRIST[side]]
    v = [w[i] - s[i] for i in range(3)]
    return math.degrees(math.asin(v[2] / math.sqrt(sum(x * x for x in v))))


def main():
    run, out = Path(sys.argv[1]), Path(sys.argv[2])
    rec = run / 'recording'
    session = json.loads((rec / 'session.json').read_text())
    sonic = json.loads((rec / 'sonic-live.json').read_text())
    log = open_text(run / 'real-controller-terminal-run7.log').read().replace('\r', '\n')
    idx = [int(x) for x in re.findall(r'Frame\[0\] \(idx=(\d+)\)', log)]
    assert idx == list(range(idx[0], idx[-1] + 1)), 'controller log skips messages'
    at = index_to_time(sonic)
    t_on, t_last = at(idx[0]), at(idx[-1])
    long_pause = max(sonic['recent_pauses'], key=lambda p: p['seconds'])
    t_stop = long_pause['start_monotonic'] + WATCHDOG_S

    poses = array.array('h')
    series = dict(t=[], latency_ms=[], left_elev=[], right_elev=[])
    resets, mask, n = [], None, 0
    all_t, all_lat = [], []
    with open_text(rec / 'motion.jsonl') as f:
        for k, line in enumerate(f):
            d = json.loads(line)
            t = d['t'] - t_on
            if d.get('model_reset'):
                resets.append(round(t, 3))
            all_t.append(t)
            all_lat.append(d['latency'] * 1e3 if d.get('latency') is not None else None)
            if k % STEP:
                continue
            body = d['robot']['body_pos_w']
            quat = d['robot']['body_quat_w']
            lift = (d.get('root_translation_estimated') or [0, 0, 0])[1]
            for p in d['joints']:
                poses.extend(int(round(c * 1000)) for c in (p[0], p[1] + lift, p[2]))
            for p in body:
                poses.extend(int(round(c * 1000)) for c in p)
            for q in quat:
                poses.extend(int(round(c * 32767)) for c in q)
            mask = mask or d.get('active_joint_mask')
            series['t'].append(round(t, 3))
            series['latency_ms'].append(round(d['latency'] * 1e3, 1))
            series['left_elev'].append(round(elevation(body, 'left'), 1))
            series['right_elev'].append(round(elevation(body, 'right'), 1))
            n += 1

    # The stop: last estimate frame before the long pause, the late frame that reset the estimate.
    gap_at, gap = None, None
    for a, b in zip(all_t, all_t[1:]):
        if 0 < b <= t_stop - t_on + 1 and b - a > 0.2:
            gap_at, gap = a, b - a
    stop_sequence = dict(last_frame_s=round(gap_at, 3), frame_gap_s=round(gap, 3), reset_s=round(gap_at + gap, 3),
                         pause_start_s=round(long_pause['start_monotonic'] - t_on, 3),
                         pause_s=round(long_pause['seconds'], 3), watchdog_s=WATCHDOG_S,
                         stop_s=round(t_stop - t_on, 3), last_received_s=round(t_last - t_on, 3))

    # Ten-second windows inside the robot window: frame rate and p95 estimation latency.
    windows = []
    start = 0.0
    while start + 10 <= t_last - t_on:
        inside = [l for t, l in zip(all_t, all_lat) if start <= t < start + 10 and l is not None]
        windows.append(dict(start_s=round(start, 1), frames_per_s=round(len(inside) / 10, 1),
                            latency_p95_ms=round(percentile(inside, 95), 1)))
        start += 10
    robot = session['robot']
    meta = dict(
        source='data/runs/20261122-174632-live-three-phone-dev',
        note='Human pose: IMUCoCo estimate. G1 pose: joint targets sent to SONIC. Not robot measurements.',
        frames=n, fps=60 / STEP, human_joints=24, g1_bodies=len(robot['body_names']),
        layout='per frame int16: human joints xyz mm (24x3), G1 body pos mm (30x3), G1 body quat wxyz x32767 (30x4)',
        parents=[-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21],
        active_joint_mask=mask,
        robot=dict(body_names=robot['body_names'], enabled_limbs=robot['enabled_limbs']),
        time_zero='robot streaming start (controller CONTROL, first received frame)',
        robot_window_s=round(t_last - t_on, 2), auto_stop_s=round(t_stop - t_on, 2),
        publication_pauses=[dict(start_s=round(p['start_monotonic'] - t_on, 3), seconds=round(p['seconds'], 3))
                            for p in sorted(sonic['recent_pauses'], key=lambda p: p['start_monotonic'])],
        model_resets_s=resets,
        stop_sequence=stop_sequence,
        latency_window_10s=windows,
        series=series)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'run7.bin').write_bytes(poses.tobytes())
    (out / 'run7.json').write_text(json.dumps(meta, separators=(',', ':')))
    print(f'{n} frames, {len(poses) * 2 / 1e6:.1f} MB poses, robot window {t_last - t_on:.1f} s, '
          f'auto stop {t_stop - t_on:.2f} s, {len(windows)} ten-second windows')


if __name__ == '__main__':
    main()
