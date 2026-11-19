/*
 * 趣味診断アプリ（仕様書 v0.2 準拠）
 * 1. 診断エンジン（純粋関数。テストや移植がしやすいよう画面と分ける）
 * 2. 計測（GA4。測定IDが空なら何もしない）
 * 3. 画面（ハッシュでルーティング: "" / #q / #r=... / #types / #hobby=ID）
 */
(function () {
  "use strict";

  const D = window.SHUMI_DATA;
  const C = window.SHUMI_CONFIG || {};
  const AXES = D.axes;
  const AXIS_IDX = Object.fromEntries(AXES.map((a, i) => [a.id, i]));
  const NQ = D.questions.length; // 5段階の質問数（12）

  /* =========================================================
     1. 診断エンジン
     ========================================================= */

  // 5段階の回答（+2〜−2）から5軸のスコア（0〜100）を出す
  function axisScores(likertAnswers) {
    const sum = AXES.map(() => 0);
    const cnt = AXES.map(() => 0);
    D.questions.forEach((q, i) => {
      const r = likertAnswers[i];
      const k = AXIS_IDX[q.axis];
      sum[k] += q.dir === "high" ? r : -r;
      cnt[k] += 1;
    });
    return sum.map((s, k) => (cnt[k] ? ((s + 2 * cnt[k]) / (4 * cnt[k])) * 100 : 50));
  }

  // 上3軸で H/L を決めて8タイプのキーにする。ちょうど50なら「100側」の質問の回答で決める。
  function typeKeyOf(scores, likertAnswers) {
    return [0, 1, 2].map(k => {
      const s = scores[k];
      if (s > 50) return "H";
      if (s < 50) return "L";
      const axisId = AXES[k].id;
      const highSum = D.questions.reduce((acc, q, i) =>
        q.axis === axisId && q.dir === "high" ? acc + likertAnswers[i] : acc, 0);
      return highSum > 0 ? "H" : "L";
    }).join("");
  }

  function hobbyKeyOf(h) { return h.v.slice(0, 3).map(x => (x >= 50 ? "H" : "L")).join(""); }

  // 合い度 0〜100（重み付きユークリッド距離を変換）
  function fit(u, hv) {
    let num = 0, wsum = 0;
    AXES.forEach((a, k) => { num += a.weight * (u[k] - hv[k]) ** 2; wsum += a.weight; });
    return 100 * (1 - Math.sqrt(num) / (100 * Math.sqrt(wsum)));
  }

  function conditionOption(key, level) {
    const c = D.conditions.find(x => x.key === key);
    return c.options.find(o => o.level === level) || c.options[c.options.length - 1];
  }

  // 値が条件の何段階目に入るか（1〜4）
  function levelOfValue(key, value) {
    const c = D.conditions.find(x => x.key === key);
    const o = c.options.find(x => value <= x.max);
    return o ? o.level : c.options[c.options.length - 1].level;
  }

  // 条件を超えた段階数に応じた減点。1段階超えるごとに PENALTY_PER_LEVEL、上限 PENALTY_MAX。
  // 一律に大きく減点すると、条件内の少数の趣味（例: 週1時間以内の2件）が性格に関係なく上位を占めるため。
  const PENALTY_PER_LEVEL = 3;
  const PENALTY_MAX = 15;
  function conditionPenalty(h, budgetLevel, timeLevel) {
    const over = Math.max(0, levelOfValue("budget", h.monthly) - budgetLevel)
               + Math.max(0, levelOfValue("time", h.hours) - timeLevel);
    return Math.min(PENALTY_MAX, over * PENALTY_PER_LEVEL);
  }

  // 予算・時間の条件。超える趣味は外す。外すと3カテゴリ未満になるなら外さず、超えた段階数に応じて減点する。
  function recommend(scores, budgetLevel, timeLevel) {
    const maxYen = conditionOption("budget", budgetLevel).max;
    const maxHours = conditionOption("time", timeLevel).max;
    const within = h => h.monthly <= maxYen && h.hours <= maxHours;
    const filtered = D.hobbies.filter(within);
    const usePenalty = new Set(filtered.map(h => h.category)).size < 3;
    const pool = usePenalty ? D.hobbies : filtered;

    const ranked = pool.map(h => {
      let f = fit(scores, h.v);
      if (usePenalty) f -= conditionPenalty(h, budgetLevel, timeLevel);
      return { hobby: h, fit: Math.max(0, Math.min(100, Math.round(f))) };
    }).sort((a, b) => b.fit - a.fit);

    const top = [];
    const seen = new Set();
    for (const r of ranked) {
      if (seen.has(r.hobby.category)) continue;
      top.push(r); seen.add(r.hobby.category);
      if (top.length === 3) break;
    }
    return { top, ranked, usedPenalty: usePenalty };
  }

  // 「意外な出会い」枠: 4位以降から、上3軸のうち1軸だけ逆の趣味を1件
  function pickSurprise(ranked, top, myKey) {
    const used = new Set(top.map(r => r.hobby.category));
    return ranked.find(r => {
      if (used.has(r.hobby.category)) return false;
      const hk = hobbyKeyOf(r.hobby);
      let diff = 0;
      for (let i = 0; i < 3; i++) if (hk[i] !== myKey[i]) diff++;
      return diff === 1;
    }) || null;
  }

  // 合う理由の一文: 趣味の特徴がはっきりしていて、ユーザーとも近い軸を2つまで
  function reasonOf(scores, h) {
    const cand = AXES.map((a, k) => ({ a, k, gap: Math.abs(scores[k] - h.v[k]), strong: Math.abs(h.v[k] - 50) }))
      .filter(x => x.strong >= 25 && x.gap <= 35)
      .sort((x, y) => x.gap - y.gap)
      .slice(0, 2);
    if (!cand.length) return "いろいろな面でバランスよく、あなたに近い趣味です。";
    const words = cand.map(x => (h.v[x.k] >= 50 ? x.a.high : x.a.low));
    return `「${words.join("」「")}」が好きなあなたに合う趣味です。`;
  }

  function diagnose(answers) {
    const likert = answers.slice(0, NQ);
    const budget = answers[NQ], time = answers[NQ + 1];
    const scores = axisScores(likert);
    const key = typeKeyOf(scores, likert);
    const rec = recommend(scores, budget, time);
    const surprise = pickSurprise(rec.ranked, rec.top, key);
    return { scores, key, type: D.types[key], budget, time, ...rec, surprise };
  }

  /* 回答を URL に入れる（DBなしで結果を開き直す・シェアするため）
     形式: #r=<版>.<12桁: 回答+2 → 0〜4><予算1〜4><時間1〜4> */
  const URL_VER = "2";
  function encodeAnswers(a) {
    return URL_VER + "." + a.slice(0, NQ).map(r => r + 2).join("") + a[NQ] + a[NQ + 1];
  }
  function decodeAnswers(s) {
    const m = /^(\d+)\.([0-4]{12})([1-4])([1-4])$/.exec(s || "");
    if (!m || m[1] !== URL_VER) return null;
    return [...m[2]].map(c => Number(c) - 2).concat([Number(m[3]), Number(m[4])]);
  }

  /* =========================================================
     2. 計測（GA4）と保存
     ========================================================= */
  function initAnalytics() {
    const id = C.gaMeasurementId;
    if (!id || !/^G-[A-Z0-9]+$/.test(id)) return;
    const s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", id);
  }
  function track(name, params) {
    if (typeof window.gtag === "function") window.gtag("event", name, params || {});
  }

  function store(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* 保存できなくても動く */ } }
  function load(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function anonId() {
    let id = load("shumi.anonId");
    if (!id) {
      id = (window.crypto && crypto.randomUUID) ? crypto.randomUUID()
        : "a-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
      store("shumi.anonId", id);
    }
    return id;
  }

  // 将来 DB の diagnoses テーブルに入れる形。MVP はブラウザ内に置くだけ。
  function buildDiagnosisRecord(answers, r) {
    return {
      anonId: anonId(),
      questionVersion: D.questionVersion,
      answers,
      scores: Object.fromEntries(AXES.map((a, k) => [a.id, Math.round(r.scores[k])])),
      type: r.key,
      top: r.top.map(x => x.hobby.id),
      createdAt: new Date().toISOString(),
    };
  }

  /* =========================================================
     3. 画面
     ========================================================= */
  const view = document.getElementById("view");
  const state = { step: 0, answers: [] };
  const TOTAL = NQ + D.conditions.length;
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const yen = n => (n === 0 ? "0円" : n >= 10000 ? `${(n / 10000).toLocaleString("ja-JP")}万円` : `${n.toLocaleString("ja-JP")}円`);
  const STEP_LABEL = { know: "知る", try: "試す", gear: "そろえる" };

  function go(hash) {
    if (location.hash === hash) route(); else location.hash = hash;
  }

  function route() {
    const h = location.hash.slice(1);
    if (h === "q") return renderQuestion();
    if (h.startsWith("r=")) {
      const a = decodeAnswers(h.slice(2));
      return a ? renderResult(a) : renderStart();
    }
    if (h === "types") return renderTypes();
    if (h.startsWith("hobby=")) return renderHobby(decodeURIComponent(h.slice(6)));
    return renderStart();
  }

  function renderStart() {
    const last = load("shumi.last");
    view.innerHTML = `
      <section class="card hero fade">
        <h1>14の質問で、<br><em>あなたに合う趣味</em>が見つかる。</h1>
        <p class="lead">あなたを8種類の動物タイプにたとえて、${D.hobbies.length}種類の趣味から合うものを3つと、ちょっと意外な出会いをひとつ提案します。</p>
        <div class="facts">
          <div class="fact"><b>14</b><span>質問</span></div>
          <div class="fact"><b>約2分</b><span>所要時間</span></div>
          <div class="fact"><b>8</b><span>動物タイプ</span></div>
        </div>
        <div class="axes-preview" aria-label="診断する5つの軸">
          ${AXES.map(a => `<span class="chip">${esc(a.low)} ↔ ${esc(a.high)}</span>`).join("")}
        </div>
        <div class="row">
          <button class="btn" id="start">診断をはじめる</button>
          ${last ? `<button class="btn ghost" id="last">前回の結果を見る</button>` : ""}
        </div>
        <button class="link" id="types">8つの動物タイプを見る →</button>
      </section>`;
    view.querySelector("#start").onclick = () => {
      state.step = 0; state.answers = [];
      track("diagnosis_start");
      go("#q");
    };
    const lb = view.querySelector("#last");
    if (lb) lb.onclick = () => go("#r=" + last);
    view.querySelector("#types").onclick = () => go("#types");
    window.scrollTo({ top: 0 });
  }

  function renderQuestion() {
    const i = state.step;
    if (i > 0 && state.answers.length < i) { state.step = 0; state.answers = []; }
    const isLikert = state.step < NQ;
    const q = isLikert ? D.questions[state.step] : D.conditions[state.step - NQ];
    const cur = state.answers[state.step];

    const options = isLikert
      ? `<div class="likert" role="group" aria-label="回答">
          ${D.likert.map(o => `
            <button class="opt" data-v="${o.value}" aria-pressed="${cur === o.value}" aria-label="${esc(o.label.replace("\n", ""))}">
              <span class="dot" aria-hidden="true"></span><span>${esc(o.label).replace("\n", "<br>")}</span>
            </button>`).join("")}
        </div>`
      : `<div class="options">
          ${q.options.map((o, k) => `
            <button class="opt" data-v="${o.level}" aria-pressed="${cur === o.level}">
              <span class="key">${"ABCD"[k]}</span><span>${esc(o.label)}</span>
            </button>`).join("")}
        </div>`;

    view.innerHTML = `
      <section class="card question fade">
        <div class="progress">
          <div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="${TOTAL}" aria-valuenow="${state.step}"><i style="width:${(state.step / TOTAL) * 100}%"></i></div>
          <span class="count">${state.step + 1} / ${TOTAL}</span>
        </div>
        <span class="qlabel">Q${state.step + 1}${isLikert ? "" : "・条件"}</span>
        <h2>${esc(q.text)}</h2>
        ${options}
        <div class="qnav">
          <button class="link" id="back" ${state.step === 0 ? "disabled" : ""}>← 前の質問へ</button>
          <button class="link" id="quit">はじめに戻る</button>
        </div>
      </section>`;

    view.querySelectorAll(".opt").forEach(b => b.onclick = () => {
      state.answers[state.step] = Number(b.dataset.v);
      view.querySelectorAll(".opt").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      setTimeout(() => {
        if (state.step + 1 < TOTAL) { state.step++; renderQuestion(); }
        else {
          const enc = encodeAnswers(state.answers);
          store("shumi.last", enc);
          const r = diagnose(state.answers);
          store("shumi.diagnosis", buildDiagnosisRecord(state.answers, r));
          track("diagnosis_complete", { type: r.key, question_version: D.questionVersion });
          go("#r=" + enc);
        }
      }, 160);
    });
    view.querySelector("#back").onclick = () => { if (state.step > 0) { state.step--; renderQuestion(); } };
    view.querySelector("#quit").onclick = () => go("");
    window.scrollTo({ top: 0 });
  }

  function radarSvg(scores) {
    const cx = 160, cy = 150, R = 100, n = AXES.length;
    const pt = (k, v) => {
      const ang = -Math.PI / 2 + (2 * Math.PI * k) / n;
      return [cx + Math.cos(ang) * R * v / 100, cy + Math.sin(ang) * R * v / 100];
    };
    const ring = v => AXES.map((_, k) => pt(k, v).map(x => x.toFixed(1)).join(",")).join(" ");
    const shape = scores.map((s, k) => pt(k, Math.max(4, s)).map(x => x.toFixed(1)).join(",")).join(" ");
    const labels = AXES.map((a, k) => {
      const [x, y] = pt(k, 128);
      const s = Math.round(scores[k]);
      const pole = s >= 50 ? a.high : a.low;
      const anchor = Math.abs(x - cx) < 8 ? "middle" : x > cx ? "start" : "end";
      return `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="${anchor}" dominant-baseline="middle">
        <tspan x="${x.toFixed(1)}" dy="-0.6em">${esc(a.name)}</tspan>
        <tspan x="${x.toFixed(1)}" dy="1.25em" class="val">${esc(pole)} ${s}</tspan></text>`;
    }).join("");
    return `<svg class="radar" viewBox="-50 0 420 300" role="img" aria-label="5軸のスコア: ${AXES.map((a, k) => `${a.name} ${Math.round(scores[k])}`).join("、")}">
      ${[25, 50, 75, 100].map(v => `<polygon class="grid" points="${ring(v)}"/>`).join("")}
      ${AXES.map((_, k) => { const [x, y] = pt(k, 100); return `<line class="grid" x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`; }).join("")}
      <polygon class="shape" points="${shape}"/>
      ${labels}
    </svg>`;
  }

  function linkFor(hobbyId, step) {
    return (D.links || []).find(l => l.hobbyId === hobbyId && l.step === step && l.active && l.url);
  }

  function stepsHtml(h, rank) {
    return `<ol class="steps">
      ${["know", "try", "gear"].map(st => {
        const l = linkFor(h.id, st);
        const body = l
          ? `<a href="${esc(l.url)}" target="_blank" rel="sponsored noopener" data-hobby="${esc(h.id)}" data-step="${st}" data-rank="${rank}" data-partner="${esc(l.partner || "")}">${esc(l.label || h.steps[st])}</a><i class="pr">PR</i>`
          : `<span>${esc(h.steps[st])}</span> <small class="policy">（リンク準備中）</small>`;
        return `<li><span class="st">${STEP_LABEL[st]}</span><span>${body}</span></li>`;
      }).join("")}
    </ol>`;
  }

  function hobbyCard(r, rank, scores) {
    const h = r.hobby;
    return `<article class="hobby ${rank === 1 ? "top" : ""}">
      <div class="hobby-head"><h4>${rank}. ${esc(h.name)}</h4><span class="fit">合い度 ${r.fit}%</span></div>
      <p class="reason">${esc(reasonOf(scores, h))}</p>
      <p>${esc(h.desc)}</p>
      <div class="meta"><span>初期費用 ${yen(h.initial)}〜</span><span>月 ${yen(h.monthly)}〜</span><span>週 ${h.hours}時間〜</span></div>
      ${stepsHtml(h, rank)}
      <button class="link" data-detail="${esc(h.id)}">${esc(h.name)}の始め方を詳しく →</button>
    </article>`;
  }

  function bindCommon() {
    view.querySelectorAll("a[data-hobby]").forEach(a => a.addEventListener("click", () => {
      track("affiliate_click", { hobby_id: a.dataset.hobby, step: a.dataset.step, rank: Number(a.dataset.rank), partner: a.dataset.partner });
    }));
    view.querySelectorAll("[data-detail]").forEach(b => b.onclick = () => go("#hobby=" + encodeURIComponent(b.dataset.detail)));
  }

  function renderResult(answers) {
    const r = diagnose(answers);
    const t = r.type;
    // シェア用の URL はタイプ別ページ（share/<KEY>.html）にする。X や LINE は # 以降を読まないため、
    // タイプ別の画像（OGP）はページを分けないと出せない。開くとすぐ結果ページ（#r=...）へ移動する。
    const base = location.href.split("#")[0].replace(/index\.html$/, "");
    const pageUrl = base + "share/" + r.key + ".html#r=" + encodeAnswers(answers);
    const shareText = `私の趣味タイプは「${t.name}」でした。おすすめは${r.top.map(x => x.hobby.name).join("・")}。 #${C.siteName || "シュミのたね"}`;
    const signup = C.signupFormUrl
      ? `<a class="btn small" href="${esc(C.signupFormUrl)}" target="_blank" rel="noopener" id="signup">公開されたら知らせてもらう</a>`
      : `<span class="policy">登録受付の準備中です。</span>`;

    view.innerHTML = `
      <section class="card fade">
        <span class="eyebrow">あなたの趣味タイプ</span>
        <div class="type-row">
          <span class="animal" aria-hidden="true">${t.animal}</span>
          <div class="type-head">
            <h2 class="type-name">${esc(t.name)}</h2>
            <span class="type-code">${esc(t.tagline)}</span>
          </div>
        </div>
        <p>${esc(t.text)}</p>
        <div class="share">
          <a class="btn small" id="share-x" href="https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(pageUrl)}" target="_blank" rel="noopener">Xでシェア</a>
          <a class="btn small" id="share-line" href="https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(pageUrl)}" target="_blank" rel="noopener">LINEで送る</a>
          <button class="btn small ghost" id="copy">リンクをコピー</button>
        </div>
      </section>

      <section class="card fade">
        <div class="section-title"><h3>あなたの5つの傾向</h3><small>0〜100</small></div>
        ${radarSvg(r.scores)}
      </section>

      <section class="card fade">
        <div class="section-title"><h3>あなたにおすすめの趣味</h3><small>${r.usedPenalty ? "条件に合う趣味が少ないため一部条件を超えるものも表示" : "予算・時間の条件に合うものから"}</small></div>
        <div class="hobby-list">${r.top.map((x, i) => hobbyCard(x, i + 1, r.scores)).join("")}</div>
      </section>

      ${r.surprise ? `
      <section class="card fade">
        <div class="surprise">
          <span class="eyebrow">意外な出会い</span>
          <h4>${esc(r.surprise.hobby.name)}</h4>
          <p>${esc(r.surprise.hobby.desc)} いつものあなたとは少し違うジャンルですが、合い度は ${r.surprise.fit}%。新しい一面が見つかるかもしれません。</p>
        </div>
        ${stepsHtml(r.surprise.hobby, 4)}
      </section>` : ""}

      <section class="card fade">
        <div class="connect">
          <span class="eyebrow">準備中</span>
          <h4>同じタイプの人とつながる</h4>
          <p>同じ趣味の人とオンラインで話せる場を準備しています。ゆくゆくは近くの人とのオフ会や地域の集まりにも広げる予定です。</p>
          ${signup}
        </div>
      </section>

      <section class="card fade">
        <div class="row">
          <button class="btn" id="retry">もう一度診断する</button>
          <button class="btn ghost" id="types">他のタイプを見る</button>
        </div>
        <p class="policy">おすすめの順位は診断の計算だけで決めていて、紹介料の高さでは変えていません。</p>
      </section>`;

    view.querySelector("#copy").onclick = () => copy(pageUrl);
    view.querySelector("#share-x").addEventListener("click", () => track("share", { method: "x", type: r.key }));
    view.querySelector("#share-line").addEventListener("click", () => track("share", { method: "line", type: r.key }));
    const su = view.querySelector("#signup");
    if (su) su.addEventListener("click", () => track("signup_click", { type: r.key }));
    view.querySelector("#retry").onclick = () => { state.step = 0; state.answers = []; track("diagnosis_start"); go("#q"); };
    view.querySelector("#types").onclick = () => go("#types");
    bindCommon();
    document.title = `${t.name} | ${C.siteName || "シュミのたね"}`;
    window.scrollTo({ top: 0 });
  }

  function renderTypes() {
    const lastEnc = load("shumi.last");
    const last = lastEnc && decodeAnswers(lastEnc);
    const myKey = last ? diagnose(last).key : null;
    const pole = (k, c) => (c === "H" ? AXES[k].high : AXES[k].low);
    view.innerHTML = `
      <section class="card fade">
        <div class="section-title"><h3>8つの動物タイプ</h3><small>場所・人数・活動量で決まります</small></div>
        <div class="type-grid">
          ${Object.entries(D.types).map(([k, t]) => `
            <div class="type-card ${k === myKey ? "me" : ""}">
              <span class="animal" aria-hidden="true">${t.animal}</span>
              <b>${esc(t.name)}${k === myKey ? "（あなた）" : ""}</b>
              <span>${[0, 1, 2].map(i => esc(pole(i, k[i]))).join(" × ")}</span>
              <span>${esc(t.tagline)}</span>
            </div>`).join("")}
        </div>
        <div class="row"><button class="btn" id="start">診断をはじめる</button></div>
        <button class="link" id="home">← トップへ</button>
      </section>`;
    view.querySelector("#start").onclick = () => { state.step = 0; state.answers = []; track("diagnosis_start"); go("#q"); };
    view.querySelector("#home").onclick = () => go("");
    document.title = `8つの動物タイプ | ${C.siteName || "シュミのたね"}`;
    window.scrollTo({ top: 0 });
  }

  function renderHobby(id) {
    const h = D.hobbies.find(x => x.id === id);
    if (!h) return renderStart();
    const t = D.types[hobbyKeyOf(h)];
    view.innerHTML = `
      <section class="card fade">
        <span class="eyebrow">${esc(h.category)}</span>
        <h2>${esc(h.name)}の始め方</h2>
        <p>${esc(h.desc)}</p>
        <div class="meta"><span>初期費用 ${yen(h.initial)}〜</span><span>月 ${yen(h.monthly)}〜</span><span>週 ${h.hours}時間〜</span></div>
        <p class="policy">特に合いやすいタイプ: ${t.animal} ${esc(t.name)}</p>
        <div class="section-title"><h3>始め方3ステップ</h3></div>
        ${stepsHtml(h, 0)}
        <div class="row"><button class="btn" id="start">自分に合うか診断する</button></div>
        <button class="link" id="back">← 戻る</button>
      </section>`;
    view.querySelector("#start").onclick = () => { state.step = 0; state.answers = []; track("diagnosis_start"); go("#q"); };
    view.querySelector("#back").onclick = () => history.back();
    bindCommon();
    document.title = `${h.name}の始め方 | ${C.siteName || "シュミのたね"}`;
    window.scrollTo({ top: 0 });
  }

  function copy(text) {
    const done = () => toast("リンクをコピーしました");
    const fallback = () => {
      const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { toast("コピーできませんでした"); }
      ta.remove();
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
    else fallback();
  }

  let toastTimer;
  function toast(msg) {
    const t = document.getElementById("toast");
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.hidden = true), 2200);
  }

  // テスト・検証用に診断エンジンだけ公開する
  window.ShumiEngine = { axisScores, typeKeyOf, fit, recommend, diagnose, encodeAnswers, decodeAnswers, hobbyKeyOf };

  initAnalytics();
  window.addEventListener("hashchange", route);
  route();
})();
