/* Replay of the three-phone run on the real G1 (2026-11-22, run 7) and the Eq. (3) elbow widget.
   Data: data/run7.bin + run7.json, built by tools/build_web_replay.py from the published logs. */
(() => {
'use strict';
const $ = s => document.querySelector(s);

/* ---------- language ---------- */
let lang = 'en';
const textNodes = [...document.querySelectorAll('[data-ko]')];
textNodes.forEach(el => { el.dataset.en = el.innerHTML; });
const T = {
  play: {en: 'Play', ko: '재생'}, pause: {en: 'Pause', ko: '일시정지'},
  before: {en: 'Robot not streaming yet', ko: '로봇 스트리밍 전'},
  on: {en: 'Robot receiving targets', ko: '로봇이 목표를 받는 중'},
  paused: {en: 'Transmission paused', ko: '전송 중단'},
  after: {en: 'After the automatic stop', ko: '자동 정지 후'},
  timeAfter: {en: s => `${s} s after robot streaming started`, ko: s => `로봇 스트리밍 시작 후 ${s} s`},
  timeBefore: {en: s => `${s} s before robot streaming started`, ko: s => `로봇 스트리밍 시작 ${s} s 전`},
  elev: {en: 'Elevation (°)', ko: '고도 (°)'}, lat: {en: 'Latency (ms)', ko: '지연 (ms)'},
  axis: {en: 'Time since robot streaming started (s)', ko: '로봇 스트리밍 시작 후 시간 (s)'},
  stop: {en: 'auto stop', ko: '자동 정지'},
  stops: {
    en: q => [
      `${q.last_frame_s.toFixed(2)} s: last estimate frame before the stop (logged). The robot's last received target maps to ${q.last_received_s.toFixed(2)} s.`,
      `${q.pause_start_s.toFixed(2)} s: no new estimate, so transmission to SONIC paused (logged).`,
      `${q.reset_s.toFixed(2)} s: the next frame came ${q.frame_gap_s.toFixed(3)} s after the previous one, over the 0.2 s limit, so the estimate was reset (logged). The phones' packets kept arriving; no phone paused for more than 44 ms around this point, so the gap arose on the laptop after reception.`,
      `about ${q.stop_s.toFixed(2)} s: the 0.5 s watchdog stopped the robot. This time is inferred as pause start + 0.5 s; the controller log has no timestamp for it. Transmission resumed at ${q.pause_end_s.toFixed(2)} s, ${q.pause_s.toFixed(3)} s after it paused, when the robot had already stopped.`],
    ko: q => [
      `${q.last_frame_s.toFixed(2)} s: 정지 전 마지막 추정 프레임(기록값). 로봇이 마지막 목표를 받은 시점은 ${q.last_received_s.toFixed(2)} s로 대응됩니다.`,
      `${q.pause_start_s.toFixed(2)} s: 새 추정이 없어 SONIC으로 보내는 전송이 멈췄습니다(기록값).`,
      `${q.reset_s.toFixed(2)} s: 다음 프레임이 ${q.frame_gap_s.toFixed(3)} s 뒤에 와서 0.2 s 한도를 넘었고, 추정을 초기화했습니다(기록값). 이 무렵 세 폰의 패킷은 44 ms 넘게 끊기지 않았으므로, 공백은 수신 뒤 노트북에서 생겼습니다.`,
      `약 ${q.stop_s.toFixed(2)} s: 0.5 s watchdog이 로봇을 정지시켰습니다. 이 시각은 전송 중단 시작 + 0.5 s로 추정한 값이며 컨트롤러 로그에는 시각이 없습니다. 전송은 ${q.pause_end_s.toFixed(2)} s, 즉 ${q.pause_s.toFixed(3)} s 뒤에 다시 시작됐고 그때 로봇은 이미 정지한 상태였습니다.`]},
  events: {
    en: [['Robot starts receiving targets'], ['Left arm raised'], ['Frame gap, estimate reset'], ['Automatic stop (inferred time)']],
    ko: [['로봇이 목표를 받기 시작'], ['왼팔 들기'], ['프레임 공백, 추정 초기화'], ['자동 정지(추정 시각)']]},
  now: {en: (l, a, b) => `At this moment: estimation latency ${l} ms · elevation target left ${a}°, right ${b}°`,
        ko: (l, a, b) => `이 순간: 추정 지연 ${l} ms · 고도 목표 왼팔 ${a}°, 오른팔 ${b}°`},
  tailFps: {en: w => `last ${(w.end_s - w.start_s).toFixed(0)} s before the stop: ${w.frames_per_s.toFixed(1)} frames/s`, ko: w => `정지 전 마지막 ${(w.end_s - w.start_s).toFixed(0)} s: ${w.frames_per_s.toFixed(1)} frames/s`},
  tailLat: {en: w => `last ${(w.end_s - w.start_s).toFixed(0)} s: ${w.latency_p95_ms.toFixed(0)} ms · not end-to-end latency`, ko: w => `마지막 ${(w.end_s - w.start_s).toFixed(0)} s: ${w.latency_p95_ms.toFixed(0)} ms · 전체 원격조작 지연 아님`},
  pauseSpan: {en: q => `${q.pause_start_s.toFixed(2)}–${q.pause_end_s.toFixed(2)} s, over the 0.5 s watchdog`, ko: q => `${q.pause_start_s.toFixed(2)}–${q.pause_end_s.toFixed(2)} s, watchdog 0.5 s 초과`},
  dist: {en: v => `${v} cm`, ko: v => `${v} cm`},
};
const t = key => T[key][lang];
function setLang(next) {
  lang = next;
  document.documentElement.lang = next;
  textNodes.forEach(el => { el.innerHTML = next === 'ko' ? el.dataset.ko : el.dataset.en; });
  document.querySelectorAll('.lang button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === next)));
  try { localStorage.setItem('lang', next); } catch (e) { /* storage unavailable */ }
  refreshText();
}
document.querySelectorAll('.lang button').forEach(b => b.addEventListener('click', () => setLang(b.dataset.lang)));
let stored = null;
try { stored = localStorage.getItem('lang'); } catch (e) { /* storage unavailable */ }
const initial = stored || ((navigator.language || '').toLowerCase().startsWith('ko') ? 'ko' : 'en');

const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/* ---------- replay state ---------- */
let meta = null, poses = null, PER = 0, idx = 0, playing = false, speed = 1, clock = 0;
let yaw = .55, pitch = .15, zoom = 185;
const human = $('#human'), robot = $('#robot'), chart = $('#chart'), seek = $('#seek');

function frameAt(k) {
  const o = k * PER, J = meta.human_joints, B = meta.g1_bodies, joints = [], pos = [], quat = [];
  for (let j = 0; j < J; j++) joints.push([poses[o + 3 * j] / 1000, poses[o + 3 * j + 1] / 1000, poses[o + 3 * j + 2] / 1000]);
  const ob = o + 3 * J;
  for (let b = 0; b < B; b++) pos.push([poses[ob + 3 * b] / 1000, poses[ob + 3 * b + 1] / 1000, poses[ob + 3 * b + 2] / 1000]);
  const oq = ob + 3 * B;
  for (let b = 0; b < B; b++) quat.push([poses[oq + 4 * b] / 32767, poses[oq + 4 * b + 1] / 32767, poses[oq + 4 * b + 2] / 32767, poses[oq + 4 * b + 3] / 32767]);
  return {joints, robot: {body_pos_w: pos, body_quat_w: quat, root_pos: pos[0]}};
}

function sizeCanvas(cv) {
  const r = cv.getBoundingClientRect(), dpr = Math.min(devicePixelRatio || 1, 2);
  const w = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  return {w: r.width, h: r.height, dpr};
}

function drawHuman(frame) {
  const {w, h, dpr} = sizeCanvas(human), ctx = human.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
  // A raised hand reaches about 2.2 m above the floor; keep it inside the canvas.
  const scale = Math.min(zoom, w * .55, h * .93 / 2.35), cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
  const proj = p => { const a = p[0] * cy + p[2] * sy, b = -p[0] * sy + p[2] * cy; return [w / 2 + a * scale, h * .93 - (p[1] * cp - b * sp) * scale]; };
  const line = (a, b, color, width, glow) => {
    ctx.beginPath(); ctx.moveTo(...proj(a)); ctx.lineTo(...proj(b));
    ctx.shadowColor = glow || 'transparent'; ctx.shadowBlur = glow ? 12 : 0;
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.stroke();
  };
  for (let i = -6; i <= 6; i++) {
    const a = .32 * Math.max(0, 1 - Math.abs(i) / 6.5);
    line([i * .25, 0, -1.5], [i * .25, 0, 1.5], `rgba(96,130,230,${a})`, 1);
    line([-1.5, 0, i * .25], [1.5, 0, i * .25], `rgba(96,130,230,${a})`, 1);
  }
  if (!frame) return;
  const parents = meta.parents;
  const pts = frame.joints.map(p => [p[0], p[1] + .96, p[2]]);
  // SMPL joints: left arm 16 18 20 22, right arm 17 19 21 23. Arms take the chart's colors.
  const side = j => ([16, 18, 20, 22].includes(j) ? 'L' : [17, 19, 21, 23].includes(j) ? 'R' : null);
  const STYLE = {L: ['#6aa6ff', 'rgba(74,140,255,.9)'], R: ['#ff9a5c', 'rgba(255,140,70,.85)'], null: ['#8292b8', null]};
  for (const pass of [null, 'L', 'R']) pts.forEach((p, j) => {
    if (parents[j] < 0 || side(j) !== pass) return;
    line(pts[parents[j]], p, STYLE[pass][0], pass ? 5.5 : 4, STYLE[pass][1]);
  });
  ctx.shadowBlur = 0;
  pts.forEach((p, j) => { ctx.beginPath(); ctx.arc(...proj(p), side(j) ? 3.6 : 3, 0, Math.PI * 2); ctx.fillStyle = side(j) ? '#eef3ff' : '#a3afc9'; ctx.fill(); });
  // Where the phones were: L and R at the wrists (joints 20, 21), P on the belt (pelvis, joint 0).
  ctx.font = '600 11px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (const [j, tag] of [[20, 'L'], [21, 'R'], [0, 'P']]) {
    const [x, y] = proj(pts[j]);
    ctx.fillStyle = 'rgba(13,19,36,.85)'; ctx.strokeStyle = '#eef3ff'; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x - 8, y - 18 - 7, 16, 14, 3) : ctx.rect(x - 8, y - 25, 16, 14); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#eef3ff'; ctx.fillText(tag, x, y - 18);
  }
}

/* ---------- chart ---------- */
let chartBase = null, chartBox = null;
function renderChart() {
  if (!meta) return;
  const {w, h, dpr} = sizeCanvas(chart), s = meta.series;
  const off = document.createElement('canvas'); off.width = chart.width; off.height = chart.height;
  const ctx = off.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const ink = css('--chart-ink'), muted = css('--muted'), line = css('--line'), shade = css('--shade');
  const L = 52, R = 12, top = 10, gap = 22, bottom = 34, plotW = w - L - R;
  const hA = (h - top - gap - bottom) * .55, hB = (h - top - gap - bottom) * .45;
  const yA = top, yB = top + hA + gap;
  const x0 = s.t[0], x1 = s.t[s.t.length - 1];
  const X = v => L + (v - x0) / (x1 - x0) * plotW;
  const YA = v => yA + (95 - v) / 190 * hA, YB = v => yB + (330 - Math.min(v, 330)) / 330 * hB;
  chartBox = {L, plotW, x0, x1};
  ctx.font = '11px system-ui, sans-serif'; ctx.textBaseline = 'middle';
  for (const [y0, hh] of [[yA, hA], [yB, hB]]) {
    ctx.fillStyle = shade;
    ctx.fillRect(X(x0), y0, X(0) - X(x0), hh);
    ctx.fillRect(X(meta.auto_stop_s), y0, X(x1) - X(meta.auto_stop_s), hh);
  }
  ctx.strokeStyle = line; ctx.lineWidth = 1; ctx.fillStyle = muted; ctx.textAlign = 'right';
  for (const v of [-90, 0, 90]) { ctx.beginPath(); ctx.moveTo(L, YA(v)); ctx.lineTo(L + plotW, YA(v)); ctx.stroke(); ctx.fillText(v, L - 6, YA(v)); }
  for (const v of [0, 100, 200, 300]) { ctx.beginPath(); ctx.moveTo(L, YB(v)); ctx.lineTo(L + plotW, YB(v)); ctx.stroke(); ctx.fillText(v, L - 6, YB(v)); }
  ctx.save(); ctx.translate(12, yA + hA / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = 'center'; ctx.fillText(t('elev'), 0, 0); ctx.restore();
  ctx.save(); ctx.translate(12, yB + hB / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = 'center'; ctx.fillText(t('lat'), 0, 0); ctx.restore();
  ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  for (let v = Math.ceil(x0 / 30) * 30; v <= x1; v += 30) ctx.fillText(v, X(v), yB + hB + 6);
  ctx.fillText(t('axis'), L + plotW / 2, yB + hB + 19);
  const path = (ys, Y, color, dash, width) => {
    ctx.beginPath(); ctx.setLineDash(dash); ctx.strokeStyle = color; ctx.lineWidth = width;
    ys.forEach((v, i) => { const px = X(s.t[i]), py = Y(v); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
    ctx.stroke(); ctx.setLineDash([]);
  };
  path(s.left_elev, YA, css('--left'), [], 1.3);
  path(s.right_elev, YA, css('--right'), [5, 3], 1.3);
  path(s.latency_ms, YB, ink, [], .8);
  ctx.strokeStyle = ink; ctx.lineWidth = 1.2; ctx.setLineDash([2, 3]);
  ctx.beginPath(); ctx.moveTo(X(meta.auto_stop_s), yA); ctx.lineTo(X(meta.auto_stop_s), yB + hB); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = ink; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
  ctx.fillText(t('stop') + ' ' + meta.auto_stop_s.toFixed(1) + ' s', X(meta.auto_stop_s) - 6, yB + 10);
  chartBase = off;
  drawChartCursor();
}
function drawChartCursor() {
  if (!chartBase) return;
  const ctx = chart.getContext('2d'), dpr = Math.min(devicePixelRatio || 1, 2);
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, chart.width, chart.height); ctx.drawImage(chartBase, 0, 0);
  const {L, plotW, x0, x1} = chartBox, x = L + (meta.series.t[idx] - x0) / (x1 - x0) * plotW;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.strokeStyle = css('--accent'); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(x, 4); ctx.lineTo(x, chart.height / dpr - 34); ctx.stroke();
}

/* ---------- drawing and timeline ---------- */
function stateKey(tt) {
  if (tt < 0) return 'before';
  if (tt <= meta.robot_window_s) return 'on';
  if (tt < meta.auto_stop_s) return 'paused';
  return 'after';
}
function draw() {
  if (!meta) return;
  const frame = frameAt(idx), tt = meta.series.t[idx];
  drawHuman(frame);
  window.drawG1Mesh(robot, frame, meta.robot, yaw, pitch, zoom, true);
  const key = stateKey(tt), chip = $('#chip');
  chip.textContent = t(key); chip.className = 'chip ' + (key === 'on' ? 'on' : key === 'after' ? 'off' : '');
  $('#time').textContent = (tt >= 0 ? t('timeAfter') : t('timeBefore'))(Math.abs(tt).toFixed(1));
  const S = meta.series;
  $('#now').textContent = t('now')(S.latency_ms[idx].toFixed(0), S.left_elev[idx].toFixed(0), S.right_elev[idx].toFixed(0));
  seek.value = idx;
  drawChartCursor();
}
function refreshText() {
  $('#play').textContent = playing ? t('pause') : t('play');
  drawElbow();
  if (!meta) return;
  const q = meta.stop_sequence;
  $('#stoplist').innerHTML = t('stops')(q).map(x => `<li>${x}</li>`).join('');
  $('#f-fps-tail').textContent = t('tailFps')(meta.latency_tail);
  $('#f-lat-tail').textContent = t('tailLat')(meta.latency_tail);
  $('#f-pause-span').textContent = t('pauseSpan')(q);
  const names = T.events[lang];
  $('#events').innerHTML = EVENTS.map((e, k) => `<button type="button" data-t="${e.t}" class="${k === EVENTS.length - 1 ? 'stopev' : ''}"><b>${e.t.toFixed(e.t % 1 ? 1 : 0)} s</b>${names[k][0]}</button>`).join('');
  // Jump a little before each event so it plays out; the stop events get a few seconds of lead-in.
  $('#events').querySelectorAll('button').forEach(b => b.addEventListener('click', () => { const v = Number(b.dataset.t); idx = indexForTime(v - (v > 100 ? 3 : 1)); clock = meta.series.t[idx]; draw(); }));
  renderChart(); draw();
}
function indexForTimeIn(ts, tt) {
  let lo = 0, hi = ts.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (ts[m] <= tt) lo = m; else hi = m - 1; }
  return lo;
}
function indexForTime(tt) { return indexForTimeIn(meta.series.t, tt); }
let EVENTS = [];
let last = null;
function tick(now) {
  if (playing && meta) {
    if (last !== null) clock += (now - last) / 1000 * speed;
    const end = meta.series.t[meta.series.t.length - 1];
    if (clock > end) clock = meta.series.t[0];
    const k = indexForTime(clock);
    if (k !== idx) { idx = k; draw(); }
  }
  last = now; requestAnimationFrame(tick);
}
function setPlaying(on) { playing = on; last = null; refreshText(); }
$('#play').addEventListener('click', () => { if (meta) { if (!playing) clock = meta.series.t[idx]; setPlaying(!playing); } });
$('#speed').addEventListener('change', e => { speed = Number(e.target.value); });
seek.addEventListener('input', () => { idx = Number(seek.value); clock = meta.series.t[idx]; draw(); });
chart.addEventListener('pointerdown', e => {
  if (!meta || !chartBox) return;
  const r = chart.getBoundingClientRect(), {L, plotW, x0, x1} = chartBox;
  const v = x0 + (e.clientX - r.left - L) / plotW * (x1 - x0);
  idx = indexForTime(Math.max(x0, Math.min(x1, v))); clock = meta.series.t[idx]; draw();
});
for (const cv of [human, robot]) {
  const ptr = new Map(); let pinch = null;
  cv.addEventListener('pointerdown', e => { ptr.set(e.pointerId, [e.clientX, e.clientY]); cv.setPointerCapture(e.pointerId); });
  cv.addEventListener('pointermove', e => {
    if (!ptr.has(e.pointerId)) return;
    const prev = ptr.get(e.pointerId); ptr.set(e.pointerId, [e.clientX, e.clientY]);
    if (ptr.size === 2) {
      const [a, b] = [...ptr.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      if (pinch) zoom = Math.max(110, Math.min(500, zoom * d / pinch));
      pinch = d;
    } else {
      yaw += (e.clientX - prev[0]) * .01; pitch = Math.max(-.6, Math.min(.7, pitch + (e.clientY - prev[1]) * .004));
    }
    draw();
  });
  const up = e => { ptr.delete(e.pointerId); pinch = null; };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  // Plain wheel scrolls the page; pinch on a trackpad (ctrlKey) or Ctrl + wheel zooms.
  cv.addEventListener('wheel', e => { if (!e.ctrlKey && !e.metaKey) return; e.preventDefault(); zoom = Math.max(110, Math.min(500, zoom - e.deltaY * .6)); draw(); }, {passive: false});
}
let resizeTimer = null;
addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { renderChart(); draw(); drawElbow(); }, 120); });
matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => { renderChart(); drawElbow(); });

async function load() {
  const [m, b] = await Promise.all([fetch('data/run7.json').then(r => r.json()), fetch('data/run7.bin').then(r => r.arrayBuffer())]);
  meta = m; poses = new Int16Array(b); PER = 3 * m.human_joints + 3 * m.g1_bodies + 4 * m.g1_bodies;
  seek.max = m.frames - 1;
  const w = m.latency_window_10s, fps = w.map(x => x.frames_per_s), lat = w.map(x => x.latency_p95_ms);
  $('#f-window').textContent = m.robot_window_s.toFixed(1) + ' s';
  m.robot.limb_tints = {left_arm: {color: [.33, .6, 1], glow: [.1, .3, .95]}, right_arm: {color: [1, .56, .3], glow: [.85, .32, .05]}};
  const S = m.series, top = S.left_elev.reduce((b, v, i) => (S.t[i] > 0 && S.t[i] < m.robot_window_s && v > S.left_elev[b] ? i : b), indexForTimeIn(S.t, 0));
  EVENTS = [{t: 0}, {t: Math.round(S.t[top])}, {t: m.stop_sequence.last_frame_s}, {t: m.auto_stop_s}];
  const span = S.t[S.t.length - 1] - S.t[0], pos = v => ((v - S.t[0]) / span * 100).toFixed(2) + '%';
  $('#band').innerHTML = `<i style="left:0;width:${pos(0)};background:var(--line)"></i>`
    + `<i style="left:${pos(0)};width:calc(${pos(m.robot_window_s)} - ${pos(0)});background:#2f9e63"></i>`
    + `<i style="left:${pos(m.auto_stop_s)};right:0;background:var(--line)"></i>`
    + `<i class="tick" style="left:${pos(m.auto_stop_s)}"></i>`;
  $('#f-fps').textContent = `${Math.min(...fps).toFixed(1)}–${Math.max(...fps).toFixed(1)} frames/s`;
  $('#f-lat').textContent = `${Math.min(...lat).toFixed(1)}–${Math.max(...lat).toFixed(1)} ms`;
  $('#f-pause').textContent = m.stop_sequence.pause_s.toFixed(3) + ' s';
  $('#loading').remove();
  idx = indexForTime(0); clock = m.series.t[idx];
  refreshText();
  if (!matchMedia('(prefers-reduced-motion: reduce)').matches) setPlaying(true);
}
load().catch(err => { $('#loading').textContent = 'Could not load the recording: ' + err.message; });
requestAnimationFrame(tick);

/* ---------- Table 1 (rounded from data/one-arm-replay/metrics.csv; checked by tools/check_paper_numbers.py) ---------- */
const TABLE1 = [
  ['1', 'IMU-only', '25.85', '517.7 / 903.1'], ['1', 'AR yaw', '25.88', '520.8 / 905.6'], ['1', 'AR IK', '17.63', '1617.9 / 3015.9'],
  ['2', 'IMU-only', '53.05', '208.7 / 328.6'], ['2', 'AR IK', '56.01', '255.3 / 431.5'], ['2 (recomp.)', 'AR IK', '22.88', '537.8 / 742.9'],
  ['3', 'IMU-only', '43.23', '610.4 / 1028.5'], ['3', 'AR IK', '12.55', '936.7 / 1461.8']];
$('#t1').innerHTML = TABLE1.map(r => `<tr class="${r[1] === 'AR IK' ? 'ar' : ''}">${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');

/* ---------- Eq. (3) elbow widget ---------- */
const LU = .28, LF = .26;  // illustrative upper-arm and forearm lengths (m)
const ecv = $('#elbowcv'), phiIn = $('#phi'), distIn = $('#dist');
let wristDir = [Math.cos(-.35), Math.sin(-.35)];  // wrist direction from the shoulder in the screen plane
const sub = (a, b) => a.map((v, i) => v - b[i]), add = (a, b) => a.map((v, i) => v + b[i]), mul = (a, k) => a.map(v => v * k);
const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0), norm = a => Math.hypot(...a), unit = a => mul(a, 1 / norm(a));
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
function elbowGeometry() {
  const d = Math.max(.1, Math.min(LU + LF - 1e-4, Number(distIn.value) / 100));
  const wrist = [wristDir[0] * d, wristDir[1] * d, 0], n = unit(wrist);
  const theta = Math.acos(Math.max(-1, Math.min(1, (d * d - LU * LU - LF * LF) / (2 * LU * LF))));
  const a = (LU * LU - LF * LF + d * d) / (2 * d), r = Math.sqrt(Math.max(0, LU * LU - a * a)), c = mul(n, a);
  let down = [0, -1, 0]; down = sub(down, mul(n, dot(down, n)));
  const u = norm(down) < 1e-6 ? unit(cross(n, [0, 0, 1])) : unit(down), v = cross(n, u);
  const phi = Number(phiIn.value) * Math.PI / 180;
  const elbow = add(c, add(mul(u, r * Math.cos(phi)), mul(v, r * Math.sin(phi))));
  return {d, theta, wrist, c, r, u, v, elbow};
}
function drawElbow() {
  const {w, h, dpr} = sizeCanvas(ecv), ctx = ecv.getContext('2d'), g = elbowGeometry();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const bg = ctx.createRadialGradient(w / 2, 0, 10, w / 2, 0, w); bg.addColorStop(0, '#18213a'); bg.addColorStop(1, '#0d1324');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h);
  const s = Math.min(w * .95, h * 1.45), ox = w * .3, oy = h * .3, ky = .32;  // oblique view: depth shifts up-right
  const P = p => [ox + (p[0] + p[2] * ky) * s, oy - (p[1] + p[2] * ky * .6) * s];
  const seg = (a, b, color, width, dash = []) => { ctx.beginPath(); ctx.setLineDash(dash); ctx.moveTo(...P(a)); ctx.lineTo(...P(b)); ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.stroke(); ctx.setLineDash([]); };
  const dotAt = (p, color, rad) => { ctx.beginPath(); ctx.arc(...P(p), rad, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill(); };
  const label = (p, text, dx = 8, dy = -8) => { const [x, y] = P(p); ctx.fillStyle = '#c7d0e6'; ctx.font = '13px system-ui, sans-serif'; ctx.fillText(text, x + dx, y + dy); };
  // body axis and reference "down"
  seg([0, .08, 0], [0, -.42, 0], 'rgba(199,208,230,.35)', 1.5, [4, 4]); label([0, -.42, 0], lang === 'ko' ? '몸통 아래 방향' : 'body down', 8, 4);
  seg([0, 0, 0], g.wrist, 'rgba(199,208,230,.45)', 1.2, [3, 4]);
  ctx.beginPath(); ctx.setLineDash([]);
  for (let k = 0; k <= 72; k++) { const a = k / 72 * Math.PI * 2, p = add(g.c, add(mul(g.u, g.r * Math.cos(a)), mul(g.v, g.r * Math.sin(a)))); const q = P(p); k ? ctx.lineTo(...q) : ctx.moveTo(...q); }
  ctx.strokeStyle = 'rgba(126,162,255,.55)'; ctx.lineWidth = 1.4; ctx.stroke();
  seg(g.c, add(g.c, mul(g.u, g.r)), 'rgba(126,162,255,.5)', 1, [2, 3]);
  seg([0, 0, 0], g.elbow, '#6f9bff', 6); seg(g.elbow, g.wrist, '#6f9bff', 6);
  dotAt([0, 0, 0], '#e6eeff', 6); dotAt(g.elbow, '#ffd27a', 6); dotAt(g.wrist, '#e6eeff', 7);
  label([0, 0, 0], lang === 'ko' ? '어깨 (IMUCoCo)' : 'shoulder (IMUCoCo)', -150, -10);
  label(g.wrist, lang === 'ko' ? '손목 (AR)' : 'wrist (AR)');
  label(g.elbow, (lang === 'ko' ? '팔꿈치' : 'elbow'));
  $('#distv').textContent = (g.d * 100).toFixed(0) + ' cm';
  $('#thetav').textContent = (g.theta * 180 / Math.PI).toFixed(1) + '°';
  $('#phiv').textContent = phiIn.value + '°';
  ecv._P = P; ecv._s = s; ecv._o = [ox, oy];
}
phiIn.addEventListener('input', drawElbow); distIn.addEventListener('input', drawElbow);
let draggingWrist = false;
const moveWrist = e => {
  const r = ecv.getBoundingClientRect(), [ox, oy] = ecv._o, x = (e.clientX - r.left - ox) / ecv._s, y = -(e.clientY - r.top - oy) / ecv._s;
  const d = Math.hypot(x, y); if (d < .02) return;
  wristDir = [x / d, y / d]; distIn.value = Math.round(Math.max(.1, Math.min(.54, d)) * 100); drawElbow();
};
ecv.addEventListener('pointerdown', e => { draggingWrist = true; ecv.setPointerCapture(e.pointerId); moveWrist(e); });
ecv.addEventListener('pointermove', e => { if (draggingWrist) moveWrist(e); });
ecv.addEventListener('pointerup', () => { draggingWrist = false; });
ecv.addEventListener('pointercancel', () => { draggingWrist = false; });

setLang(initial);
})();
