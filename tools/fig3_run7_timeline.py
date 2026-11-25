"""Fig. 3: run 7 on the physical G1 (11/22), from the raw recording.

(a) G1 arm elevation targets (shoulder-to-wrist vector vs horizontal) computed
    from the retargeted body positions in motion.jsonl.
(b) Per-frame estimation latency (motion.jsonl `latency`: sample time to finished
    estimate, engine.py:846 @ b2a59f1). The dotted line is the watchdog's automatic stop.
    Publication pauses are no longer shaded (2026-11-24, author direction); they are
    still used to place the robot window on the time axis.

The robot's CONTROL start and watchdog stop are placed on the Studio clock by
mapping the controller's first and last received frame indices (frame index =
publisher message counter, sonic_live.py:117) onto the publishing timeline.

    python3 tools/fig3_run7_timeline.py   # needs numpy and matplotlib

Reads the public run folder (data/runs/20261122-174632-live-three-phone-dev, .xz files) and
writes figures/fig3_run7_timeline.png and .json. Copied from the paper's figure script; only the
input paths changed.
"""

import json
import lzma
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'figures'
RUN = ROOT / 'data/runs/20261122-174632-live-three-phone-dev'
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'   # validated categorical slots 1-3
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#d9d8d4'


def load(rec):
    t, lat, elev_l, elev_r = [], [], [], []
    with lzma.open(rec / 'motion.jsonl.xz', 'rt') as f:
        for line in f:
            d = json.loads(line)
            body = np.asarray(d['robot']['body_pos_w'])
            t.append(d['t'])
            lat.append(d['latency'])
            for s, w, out in ((16, 20, elev_l), (23, 27, elev_r)):   # shoulder_pitch_link, wrist_roll_link
                v = body[w] - body[s]
                out.append(np.degrees(np.arcsin(v[2] / np.linalg.norm(v))))
    sonic = json.loads((rec / 'sonic-live.json').read_text())
    return np.array(t), np.array(lat) * 1e3, np.array(elev_l), np.array(elev_r), sonic


WATCHDOG_S = 0.5    # sonic_controller.py watchdog timeout (real-controller-run7.json)
PUBLISH_HZ = 50.0   # sonic_live.py publishes the pose topic at 50 Hz; the controller log confirms it (see main)


def index_to_time(sonic):
    """Map a publisher message index to Studio time, skipping publication pauses.

    The first send time is not recorded, so it is recovered from the last send time, the number of
    published messages and the recorded pauses at the 50 Hz publish rate.
    """
    pauses = sorted((p['start_monotonic'], p['end_monotonic']) for p in sonic['recent_pauses'])
    assert len(pauses) == sonic['pause_count'], 'pause list is truncated'
    first_send = sonic['last_send_monotonic'] - sonic['published'] / PUBLISH_HZ - sum(e - s for s, e in pauses)

    def at(k):
        t, remaining = first_send, k / PUBLISH_HZ
        for s, e in pauses:
            if t + remaining <= s:
                break
            remaining -= s - t
            t = e
        return t + remaining
    return at, first_send


def main():
    rec, log = RUN / 'recording', RUN / 'real-controller-terminal-run7.log.xz'
    t, lat, el, er, sonic = load(rec)
    text = lzma.open(log, 'rt', errors='replace').read().replace('\r', '\n')
    # First frame index of each pose message the controller decoded (consecutive, one per message).
    idx = [int(x) for x in re.findall(r'Frame\[0\] \(idx=(\d+)\)', text)]
    assert idx == list(range(idx[0], idx[-1] + 1)), 'controller log skips messages'
    decode_ms = [int(x) for x in re.findall(r'Decode interval: (\d+) ms', text)]
    at, first_send = index_to_time(sonic)
    t_on, t_last = at(idx[0]), at(idx[-1])
    # Checks on the mapping: the controller-side receive span matches, and the last message the robot
    # received sits just before the one pause longer than the 0.5 s watchdog.
    long_pause = max(sonic['recent_pauses'], key=lambda p: p['seconds'])
    assert abs((t_last - t_on) - sum(decode_ms) / 1e3) < 0.5, (t_last - t_on, sum(decode_ms) / 1e3)
    assert abs(t_last - long_pause['start_monotonic']) < 0.2, (t_last, long_pause)
    t_off = long_pause['start_monotonic'] + WATCHDOG_S   # watchdog sends O after 0.5 s without messages
    t0 = t_on
    x = t - t0
    keep = (x > -12) & (x < (t_off - t0) + 12)

    plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 7, 'axes.edgecolor': MUTED,
                         'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                         'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})
    fig, (a, b) = plt.subplots(2, 1, figsize=(3.07, 1.6), sharex=True,
                               gridspec_kw={'height_ratios': [1.25, 1], 'hspace': 0.28})
    for ax in (a, b):
        ax.grid(axis='y', color=GRID, linewidth=0.5)
        ax.spines[['top', 'right']].set_visible(False)
        ax.axvspan(-12, 0, color='#f0efec', lw=0)
        ax.axvspan(t_off - t0, x[keep].max(), color='#f0efec', lw=0)
    a.plot(x[keep], el[keep], color=BLUE, lw=1.0, label='Left arm')
    a.plot(x[keep], er[keep], color=ORANGE, lw=1.0, ls=(0, (3, 1.5)), label='Right arm')
    a.set_ylabel('Elevation (°)')
    a.set_ylim(-95, 95)
    a.set_yticks([-90, 0, 90])
    a.legend(loc='lower right', bbox_to_anchor=(1.0, 0.97), ncol=2, frameon=False, handlelength=2.2, borderaxespad=0.0)
    a.text(2, 88, 'robot following →', color=MUTED, fontsize=6.5, va='top')
    b.plot(x[keep], lat[keep], color=INK, lw=0.5)
    for ax in (a, b):
        ax.axvline(t_off - t0, color=INK, lw=0.8, ls=':')
    b.text(t_off - t0 - 7, 285, 'auto stop', ha='right', va='center', fontsize=6.5, color=INK)
    b.set_ylim(0, 320)
    b.set_yticks([0, 100, 200, 300])
    b.set_ylabel('Est. latency (ms)')
    b.set_xlabel('Time since robot streaming started (s)')
    b.set_xlim(-12, (t_off - t0) + 12)
    fig.align_ylabels((a, b))
    for ax, tag in ((a, '(a)'), (b, '(b)')):
        ax.text(0.0, 1.03, tag, transform=ax.transAxes, fontsize=7.5, fontweight='bold', ha='left', va='bottom')
    out = HERE / 'fig3_run7_timeline.png'
    fig.savefig(out, dpi=400, bbox_inches='tight', pad_inches=0.02, facecolor='white')
    inside = (x >= 0) & (x <= t_last - t0)
    summary = dict(robot_window_s=round(t_last - t0, 1), messages_received=len(idx),
                   controller_receive_span_s=round(sum(decode_ms) / 1e3, 1),
                   controller_mean_interval_ms=round(sum(decode_ms) / len(decode_ms), 2),
                   first_send_after_recording_start_s=round(first_send - float(t[0]), 2),
                   last_message_before_long_pause_s=round(long_pause['start_monotonic'] - t_last, 3),
                   estimation_latency_ms_p50=round(float(np.percentile(lat[inside], 50)), 1),
                   estimation_latency_ms_p95=round(float(np.percentile(lat[inside], 95)), 1),
                   elevation_range_deg={'left': [round(float(el[inside].min()), 1), round(float(el[inside].max()), 1)],
                                        'right': [round(float(er[inside].min()), 1), round(float(er[inside].max()), 1)]})
    (HERE / 'fig3_run7_timeline.json').write_text(json.dumps(summary, indent=2))
    print('wrote', out, summary)


if __name__ == '__main__':
    main()
