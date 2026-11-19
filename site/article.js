/*
 * 記事ページ（site/hobby/*.html）用の小さなスクリプト。
 * 1. GA4（config.js の測定IDが空なら何もしない）
 * 2. 始め方3ステップに、data.js の links からアフィリエイトリンクを入れる（PR 表記と rel="sponsored" 付き）
 * 3. リンクのクリックと、診断ボタンのクリックを計測する
 */
(function () {
  "use strict";
  var C = window.SHUMI_CONFIG || {};
  var D = window.SHUMI_DATA || {};

  var id = C.gaMeasurementId;
  if (id && /^G-[A-Z0-9]+$/.test(id)) {
    var s = document.createElement("script");
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

  var links = D.links || [];
  document.querySelectorAll(".slot[data-hobby]").forEach(function (slot) {
    var hobby = slot.getAttribute("data-hobby");
    var step = slot.getAttribute("data-step");
    var l = links.filter(function (x) { return x.hobbyId === hobby && x.step === step && x.active && x.url; })[0];
    if (!l || !/^https:\/\//.test(l.url)) return;
    var a = document.createElement("a");
    a.href = l.url;
    a.target = "_blank";
    a.rel = "sponsored noopener";
    a.textContent = l.label || slot.textContent;
    a.addEventListener("click", function () {
      track("affiliate_click", { hobby_id: hobby, step: step, rank: 0, partner: l.partner || "", page: "article" });
    });
    var pr = document.createElement("i");
    pr.className = "pr";
    pr.textContent = "PR";
    slot.textContent = "";
    slot.appendChild(a);
    slot.appendChild(pr);
  });

  document.querySelectorAll("[data-cta]").forEach(function (el) {
    el.addEventListener("click", function () {
      track("article_cta_click", { cta: el.getAttribute("data-cta"), page: location.pathname });
    });
  });
})();
