'use strict';
// 하루마켓 리뷰 온도계 화면. 수강생은 이 파일을 고치지 않습니다.
// 응답 필드는 SPEC.md와 SPEC_COUPON.md에 정의된 이름만 읽습니다. 없으면 화면에 경고로 보여 줍니다.

const $ = (id) => document.getElementById(id);

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, '');
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

/* ---------- 응답 필드 검사 ---------- */
const has = (o, k) => o !== null && typeof o === 'object' && k in o && o[k] !== undefined && o[k] !== null;
const missing = (k) => h('span', { class: 'missing' }, `⚠ 응답에 '${k}' 필드가 없습니다`);
const val = (o, k, fmt) => (has(o, k) ? (fmt ? fmt(o[k]) : String(o[k])) : missing(k));
const isNum = (v) => typeof v === 'number' && isFinite(v);

/* ---------- 상태 pill (실패하면 5초마다 다시 확인) ---------- */
const pill = $('status-pill');
async function checkHealth() {
  let ok = false;
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 6000);
    const r = await fetch('/health', { signal: ctl.signal, cache: 'no-store' });
    clearTimeout(t);
    ok = r.ok;
  } catch (e) { ok = false; }
  pill.textContent = ok ? 'API 연결됨' : 'API 대기 중';
  pill.className = 'pill ' + (ok ? 'pill-ok' : 'pill-wait');
  if (!ok) setTimeout(checkHealth, 5000);
}

/* ---------- API 호출 ---------- */
async function post(url, body) {
  let res;
  try {
    res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  } catch (e) { return { network: true, status: 0, raw: String(e) }; }
  const text = await res.text();
  let json; try { json = JSON.parse(text); } catch (e) { json = undefined; }
  return { status: res.status, ok: res.ok, json, raw: text };
}

function showRaw(box, label, r, reqBody) {
  const body = r.network ? r.raw : (r.json !== undefined ? JSON.stringify(r.json, null, 2) : (r.raw || '(본문 없음)'));
  box.replaceChildren(h('details', {},
    h('summary', {}, `응답 원문 보기 · ${label} · ${r.network ? '연결 실패' : 'HTTP ' + r.status}`),
    h('pre', {}, '요청\n' + JSON.stringify(reqBody, null, 2)),
    h('pre', {}, '응답\n' + body)));
}

/* ---------- 오류 문구 ---------- */
const FIELD_KO = { text: '리뷰 내용', rating: '별점', review_id: '리뷰 번호' };
function fieldMessages(detail) {
  if (!Array.isArray(detail)) return [typeof detail === 'string' ? detail : '입력을 확인해 주세요.'];
  return detail.map((d) => {
    const name = FIELD_KO[(d.loc || []).filter((p) => p !== 'body').join('.')] || '입력';
    const t = d.type || '';
    if (t.includes('too_short') || t === 'missing') return `${name}: 비어 있어요. 내용을 써 주세요.`;
    if (t.includes('too_long')) return `${name}: 너무 길어요. 500자까지 쓸 수 있어요.`;
    if (name === '별점') return `${name}: 1~5 중에서 골라 주세요.`;
    return `${name}: ${d.msg || '값을 확인해 주세요.'}`;
  });
}
function errorInfo(r, what) {
  if (r.network) return { kind: 'err', lines: ['서버에 연결할 수 없어요. 서버가 켜져 있는지 확인해 주세요.'] };
  if (r.status === 422) return { kind: 'err', lines: fieldMessages(r.json && r.json.detail) };
  if (r.status === 501) {
    const d = r.json && r.json.detail ? r.json.detail : '아직 구현되지 않았습니다';
    return { kind: 'todo', lines: [`아직 구현되지 않았어요: ${d.replace(/^아직 구현되지 않았습니다:\s*/, '')} — 세션 2/4에서 AI와 함께 만들어요`] };
  }
  // 쿠폰 주소에 POST를 받는 곳이 없으면 404 또는 405가 온다 (세션 4에서 쿠폰 API를 만들기 전)
  if (what === 'coupon' && (r.status === 404 || r.status === 405)) {
    return { kind: 'todo', lines: ['쿠폰 API가 아직 없어요. 세션 4에서 명세(SPEC_COUPON.md)를 보고 만듭니다.'] };
  }
  if (r.status === 503) return { kind: 'err', lines: ['AI 부품이 아직 준비 중이거나 응답하지 않아요. 잠시 뒤 다시 눌러 주세요. (처음에는 모델을 불러오느라 시간이 걸려요)'] };
  return { kind: 'err', lines: [`예상하지 못한 응답이에요 (HTTP ${r.status}). 아래 '응답 원문'을 확인해 보세요.`] };
}

/* ---------- 입력 상태 ---------- */
const state = { rating: 5, reviewId: null, sampleText: null, typedCount: 0, analyzed: null };
const textEl = $('text');

function renderStars() {
  const box = $('stars');
  box.replaceChildren(
    ...[1, 2, 3, 4, 5].map((n) => h('button', {
      type: 'button', role: 'radio', class: n <= state.rating ? 'on' : '',
      'aria-checked': String(n === state.rating), 'aria-label': `${n}점`,
      onclick: () => { state.rating = n; renderStars(); },
    }, '★')),
    h('span', { class: 'rating-text' }, `${state.rating}점`));
}

function updateCount() {
  const n = textEl.value.length;
  const c = $('count');
  c.textContent = `${n} / 500`;
  c.className = 'counter' + (n > 500 ? ' over' : '');
}
textEl.addEventListener('input', () => {
  updateCount();
  if (state.reviewId && textEl.value !== state.sampleText) { // 샘플을 고쳐 쓰면 내가 쓴 리뷰로 취급
    state.reviewId = null; state.sampleText = null; markActive(null);
  }
});

/* ---------- 샘플 리뷰 ---------- */
let sampleButtons = {};
function markActive(id) {
  for (const [rid, b] of Object.entries(sampleButtons)) b.classList.toggle('active', rid === id);
}
async function loadSamples() {
  const box = $('samples');
  try {
    const data = await (await fetch('samples.json')).json();
    box.replaceChildren();
    for (const p of data.products) {
      box.append(h('h3', { class: 'prod' }, p.name));
      for (const rv of p.reviews) {
        const b = h('button', {
          type: 'button', class: 'sample',
          onclick: () => {
            textEl.value = rv.text; state.rating = rv.rating; state.reviewId = rv.review_id; state.sampleText = rv.text;
            renderStars(); updateCount(); markActive(rv.review_id); textEl.focus();
          },
        }, h('div', { class: 'meta' }, '★'.repeat(rv.rating), h('span', {}, `${rv.review_id} · ${p.name}`)), rv.text);
        sampleButtons[rv.review_id] = b;
        box.append(b);
      }
    }
  } catch (e) { box.textContent = '샘플 리뷰를 불러오지 못했어요.'; }
}

/* ---------- 결과 그리기 ---------- */
function showError(info) {
  const box = $('error');
  box.className = 'error' + (info.kind === 'todo' ? ' todo' : '');
  box.replaceChildren(info.lines.length === 1 ? info.lines[0] : h('ul', {}, info.lines.map((l) => h('li', {}, l))));
  box.hidden = false;
}

function renderResult(j) {
  const badges = h('div', { class: 'badges' },
    has(j, 'label')
      ? h('span', { class: 'badge ' + (j.label === 'positive' ? 'positive' : 'negative') }, j.label === 'positive' ? '긍정' : j.label === 'negative' ? '부정' : j.label)
      : missing('label'),
    has(j, 'mismatch')
      ? (j.mismatch ? h('span', { class: 'badge warn' }, '⚠ 별점과 내용이 반대예요') : null)
      : missing('mismatch'));
  const t = has(j, 'temperature') && isNum(j.temperature) ? j.temperature : null;
  const pct = t === null ? 0 : Math.max(0, Math.min(100, t));
  const therm = t === null ? null : h('div', {},
    h('div', { class: 'thermo', role: 'img', 'aria-label': `리뷰 온도 ${t}도` },
      h('div', { class: 'cover', style: `width:${100 - pct}%` }),
      h('div', { class: 'mark', style: `left:${pct}%` })),
    h('div', { class: 'scale' }, h('span', {}, '0℃'), h('span', {}, '50℃'), h('span', {}, '100℃')));
  $('result').replaceChildren(
    badges,
    h('div', { class: 'temp-big' }, has(j, 'temperature') ? [String(j.temperature), h('small', {}, ' ℃')] : missing('temperature')),
    h('div', { class: 'score-line' }, '점수(긍정일 확률): ', val(j, 'score')),
    therm);
}

/* ---------- 분석 ---------- */
$('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = $('analyze-btn');
  const id = state.reviewId || `my-${++state.typedCount}`;
  const body = { text: textEl.value, rating: state.rating };
  btn.disabled = true;
  $('error').hidden = true;
  const r = await post('/v1/reviews/analyze', body);
  btn.disabled = false;
  $('result-card').hidden = false;
  showRaw($('analyze-raw'), '분석', r, body);
  $('coupon-result').replaceChildren();
  $('coupon-raw').replaceChildren();
  if (r.ok && r.json) {
    state.analyzed = { review_id: id, text: textEl.value };
    renderResult(r.json);
    $('coupon-btn').disabled = false;
  } else {
    state.analyzed = null;
    $('result').replaceChildren();
    $('coupon-btn').disabled = true;
    showError(errorInfo(r));
    if (r.network) $('result-card').hidden = false;
  }
});

/* ---------- 쿠폰 발급 ---------- */
const TYPE_KO = { APOLOGY: '사과', THANKS: '감사' };
$('coupon-btn').addEventListener('click', async () => {
  if (!state.analyzed) return;
  const btn = $('coupon-btn');
  const body = { review_id: state.analyzed.review_id, text: state.analyzed.text };
  btn.disabled = true;
  const r = await post('/v1/coupons/issue', body);
  btn.disabled = false;
  showRaw($('coupon-raw'), '쿠폰', r, body);
  const out = $('coupon-result');
  if (!r.ok) {
    const info = errorInfo(r, 'coupon');
    out.replaceChildren(h('div', { class: 'chip ' + (info.kind === 'todo' ? 'todo' : 'err') }, info.lines.join(' ')));
    return;
  }
  const j = r.json;
  if (!has(j, 'issued')) { out.replaceChildren(h('div', { class: 'chip err' }, missing('issued'))); return; }
  if (!j.issued) { out.replaceChildren(h('div', { class: 'chip info' }, '쿠폰 대상이 아니에요')); return; }
  out.replaceChildren(h('div', { class: 'chip' },
    `${has(j, 'coupon_type') ? (TYPE_KO[j.coupon_type] || j.coupon_type) : '?'} 쿠폰 · `,
    has(j, 'amount') ? `${Number(j.amount).toLocaleString('ko-KR')}원` : missing('amount'),
    ' · ', has(j, 'code') ? h('code', {}, j.code) : missing('code')));
});

$('coupon-btn').disabled = true;
renderStars();
updateCount();
loadSamples();
checkHealth();
