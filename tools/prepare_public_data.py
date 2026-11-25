#!/usr/bin/env python3
"""Build the public data/ folder from the team's raw run archive.

The raw archive (SHAPE_G1_MSI_runs_20261122-1815.tar, sha256 6fc4377a...f861) is not
public. This script documents exactly what was copied and how it was cleaned:

* Phone identifiers (device_id, session_id, ar_reference_id and the UUID inside clock_id)
  are replaced by stable pseudonyms such as ``ios-left-arm``. Every other field is kept.
* Non-loopback IPv4 addresses and home directories on the field laptop are replaced by
  placeholders (``<lan-ip-1>``, ``~``).
* Large logs are stored as .xz. Nothing else is changed: timestamps, sensor values,
  estimates and controller output keep their recorded values.

    python3 tools/prepare_public_data.py <extracted archive root> data/runs
"""
import csv
import hashlib
import json
import lzma
import re
import shutil
import sys
from pathlib import Path

UUID = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}')
IPV4 = re.compile(r'(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])')
KEEP_IP = {'127.0.0.1', '0.0.0.0'}
HOME = re.compile(r'/home/[A-Za-z0-9_.-]+')

RUNS = {
    # 1st demonstration: one iOS phone in the right hand (2026-11-21).
    'runs-1121/20261121-215716-g1-supported-one-iphone': dict(
        copy=['o-sent.json', 'real-controller.json', 'real-controller-run1.json', 'real-controller-run2.json',
              'studio.log', 'probe-physical.log', 'probe-physical/summary.json',
              'recording/session.json', 'recording/calibration.json', 'recording/sonic-live.json'],
        xz=['recording/raw.jsonl', 'real-controller-terminal-run1.log', 'real-controller-terminal-run2.log',
            'real-controller-terminal.log'],
        slim_motion=True),
    # 2nd demonstration, last three-phone run on the real G1 (run 7, 2026-11-22).
    'runs-1122/20261122-174632-live-three-phone-dev': dict(
        copy=['real-controller.json', 'real-controller-run7.json', 'studio-live.log',
              'recording/session.json', 'recording/calibration.json', 'recording/sonic-live.json'],
        xz=['recording/raw.jsonl', 'recording/motion.jsonl', 'real-controller-terminal-run7.log'],
        slim_motion=False),
}
# Controller results of the other three-phone runs (no recordings published).
EXTRA = ['runs-1122/20261122-164557-live-three-phone-dev/real-controller-run1.json',
         'runs-1122/20261122-165904-live-three-phone-dev/real-controller-run2.json',
         'runs-1122/20261122-173810-live-three-phone-dev/real-controller-run6.json']
# Launch scripts used on the field laptop.
SCRIPTS = ['relay/real-1121/1-studio-live.sh', 'relay/real-1121/3-real-controller-HUMAN-ONLY.sh',
           'relay/real-1122/1-studio-live-3phone.sh', 'relay/real-1122/3-real-controller-HUMAN-ONLY.sh']


class Scrubber:
    """Pseudonyms are named after the phone's OS and the body role it streamed most."""
    KINDS = {'device_id': 'device', 'session_id': 'session', 'ar_reference_id': 'ar-ref'}

    def __init__(self):
        self.ids, self.ips, self.counts = {}, {}, {}
        self.role, self.os = {}, {}

    def prescan(self, path):
        from collections import Counter
        for line in path.open():
            p = json.loads(line).get('packet')
            if not isinstance(p, dict):
                continue
            values = [p[k] for k in self.KINDS if k in p]
            if 'clock_id' in p:
                values.append(p['clock_id'].rpartition('_')[2])
            for v in values:
                if p.get('stream_id'):
                    self.role.setdefault(v, Counter())[p['stream_id']] += 1
                if 'clock_id' in p:
                    self.os.setdefault(v, Counter())['ios' if p['clock_id'].startswith('apple') else 'android'] += 1

    def pseudonym(self, value, kind):
        key = (kind, value)
        if key not in self.ids:
            role = self.role.get(value)
            osn = self.os.get(value)
            base = '-'.join([osn.most_common(1)[0][0] if osn else 'phone', kind,
                             role.most_common(1)[0][0].replace('_', '-') if role else 'unknown'])
            n = self.counts.get(base, 0) + 1
            self.counts[base] = n
            self.ids[key] = base if n == 1 else f'{base}-{n}'
        return self.ids[key]

    def text(self, s):
        s = HOME.sub('~', s)

        def ip(m):
            a = m.group(1)
            if a in KEEP_IP:
                return a
            self.ips.setdefault(a, f'<lan-ip-{len(self.ips) + 1}>')
            return self.ips[a]
        s = IPV4.sub(ip, s)
        # Any remaining UUID (should not occur outside raw packets) becomes a neutral token.
        return UUID.sub(lambda m: self.pseudonym(m.group(0), 'id'), s)

    def packet(self, p):
        for k, kind in self.KINDS.items():
            if k in p:
                # A session's clock_id carries the same UUID as its session_id.
                p[k] = self.pseudonym(p[k], 'session' if kind == 'session' else kind)
        if 'clock_id' in p:
            prefix, _, uid = p['clock_id'].rpartition('_')
            p['clock_id'] = prefix + '_' + self.pseudonym(uid, 'session')
        return p


def write_xz(path, data):
    with lzma.open(path, 'wb', preset=9) as f:
        f.write(data)


def raw_lines(src, scrub):
    out = []
    for line in src.open():
        d = json.loads(line)
        if isinstance(d.get('packet'), dict):
            scrub.packet(d['packet'])
        out.append(json.dumps(d, separators=(', ', ': ')))
    return ('\n'.join(out) + '\n').encode()


def slim_motion(src, dst, joint_names):
    """Per-frame timing and live G1 arm targets from a large motion.jsonl (11/21 run)."""
    arm = [i for i, n in enumerate(joint_names) if 'shoulder' in n or 'elbow' in n or 'wrist' in n]
    with src.open() as f, dst.open('w', newline='') as g:
        w = csv.writer(g)
        w.writerow(['t', 'latency_s', 'model_reset', 'g1_segment_start'] + [joint_names[i] for i in arm])
        for line in f:
            d = json.loads(line)
            q = d.get('robot', {}).get('joint_pos')
            w.writerow([repr(d['t']), repr(d['latency']) if d.get('latency') is not None else '',
                        int(bool(d.get('model_reset'))), int(bool(d.get('g1_segment_start')))]
                       + ([f'{q[i]:.6f}' for i in arm] if q else [''] * len(arm)))


def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    scrub = Scrubber()
    out.mkdir(parents=True, exist_ok=True)
    for rel in RUNS:
        scrub.prescan(root / rel / 'recording/raw.jsonl')
    for rel, plan in RUNS.items():
        src, dst = root / rel, out / Path(rel).name
        for name in plan['copy']:
            (dst / name).parent.mkdir(parents=True, exist_ok=True)
            (dst / name).write_text(scrub.text((src / name).read_text(errors='replace')))
        for name in plan['xz']:
            (dst / name).parent.mkdir(parents=True, exist_ok=True)
            data = raw_lines(src / name, scrub) if name.endswith('raw.jsonl') else \
                scrub.text((src / name).read_text(errors='replace')).encode()
            write_xz(dst / (name + '.xz'), data)
        if plan['slim_motion']:
            names = json.loads((src / 'recording/session.json').read_text())['robot']['joint_names']
            slim = dst / 'recording/motion-slim.csv'
            slim_motion(src / 'recording/motion.jsonl', slim, names)
            write_xz(slim.with_suffix('.csv.xz'), slim.read_bytes())
            slim.unlink()
        print('wrote', dst)
    extra = out / 'other-three-phone-runs'
    extra.mkdir(exist_ok=True)
    for rel in EXTRA:
        p = Path(rel)
        (extra / f'{p.parent.name}__{p.name}').write_text(scrub.text((root / rel).read_text()))
    scripts = out.parent / 'launch-scripts'
    for rel in SCRIPTS:
        p = Path(rel)
        (scripts / p.parent.name).mkdir(parents=True, exist_ok=True)
        (scripts / p.parent.name / p.name).write_text(scrub.text((root / rel).read_text()))
    (out.parent / 'pseudonyms.json').write_text(json.dumps(dict(
        note='Original identifiers are withheld; only the pseudonym list and counts are published.',
        identifiers=sorted(set(scrub.ids.values())), lan_ip_placeholders=sorted(scrub.ips.values())), indent=2) + '\n')
    sums = []
    for f in sorted(p for p in out.parent.rglob('*') if p.is_file() and p.name != 'SHA256SUMS'):
        sums.append(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(out.parent)}')
    (out.parent / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')


if __name__ == '__main__':
    main()
