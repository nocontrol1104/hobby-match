"""
趣味の記事ページ（始め方ガイド）を作るスクリプト。

  python tools/build_articles.py

読むもの:
  content/hobbies/<趣味ID>.md   記事の本文（Markdown の一部だけ使える。下の md_to_html を参照）
  site/data.js                  趣味マスタ（名前・費用・時間・始め方3ステップ）とタイプ
  site/config.js                公開先の URL（siteUrl）

作るもの:
  site/hobby/<趣味ID>.html      記事ページ
  site/hobby/index.html         記事の一覧
  site/articles.js              記事がある趣味ID の一覧（診断画面から記事へリンクするため）
  site/sitemap.xml              検索エンジン向けのページ一覧

費用・時間・始め方3ステップは data.js から入れるので、記事の本文には書かない（数字がずれないように）。
アフィリエイトリンクは data.js の links から、ページを開いたときに site/article.js が入れる。
data.js を読むために Chrome / Edge のヘッドレスモードを使う（tools/build_ogp.py と同じ）。
"""
import datetime
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_ogp import find_browser, read_site_url  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CONTENT = ROOT / "content" / "hobbies"
STEP_LABEL = {"know": "知る", "try": "試す", "gear": "そろえる"}


# ---------- データの読み込み ----------

def load_data(browser):
    """site/data.js をブラウザで読み込み、window.SHUMI_DATA を JSON で受け取る。"""
    page = (
        '<!doctype html><meta charset="utf-8"><pre id="out"></pre>'
        f'<script src="{(SITE / "data.js").as_uri()}"></script>'
        '<script>document.getElementById("out").textContent = JSON.stringify(window.SHUMI_DATA);</script>'
    )
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "dump.html"
        f.write_text(page, encoding="utf-8")
        dom = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp}/profile",
             "--allow-file-access-from-files", "--virtual-time-budget=3000", "--dump-dom", f.as_uri()],
            capture_output=True, timeout=120,
        ).stdout.decode("utf-8", "replace")
    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m or not m.group(1).strip():
        sys.exit("site/data.js を読み込めませんでした。")
    return json.loads(html.unescape(m.group(1)))


def read_article(path):
    """先頭の --- で囲んだ部分（updated: 2026-11-19 など）と本文に分ける。"""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta = {}
    if text.startswith("---\n"):
        head, _, text = text[4:].partition("\n---\n")
        for line in head.splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, text.strip()


# ---------- Markdown（使うものだけ） ----------

def inline(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def md_to_html(text):
    """使える書き方: ## 見出し / ### 小見出し / - 箇条書き / **太字** / 空行で段落を分ける。"""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in text.split("\n"):
        line = line.rstrip()
        if not line:
            flush()
        elif line.startswith("### "):
            flush(); out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            flush(); out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:])
        else:
            if items:
                flush()
            para.append(line)
    flush()
    return "\n".join(out)


# ---------- 部品 ----------

def yen(n):
    if n == 0:
        return "0円"
    if n >= 10000:
        v = n / 10000
        return f"{v:g}万円"
    return f"{n:,}円"


def type_key(h):
    return "".join("H" if x >= 50 else "L" for x in h["v"][:3])


def distance(a, b, axes):
    return sum(ax["weight"] * (x - y) ** 2 for ax, x, y in zip(axes, a["v"], b["v"])) ** 0.5


def e(s):
    return html.escape(str(s))


HEAD = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<!-- tools/build_articles.py が生成するファイル。直接編集しない（本文は content/hobbies/ を直す）。 -->
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="シュミのたね">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}ogp/default.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8C%B1%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&family=Noto+Sans+JP:wght@400;500;700&display=swap">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="app">
  <p class="pr-notice">本ページはプロモーションが含まれています</p>
  <header class="brand">
    <a class="logo" href="../" style="color:inherit;text-decoration:none"><span class="logo-dot" aria-hidden="true"></span>シュミのたね</a>
  </header>
"""

FOOT = """  <p class="foot"><a href="../">趣味診断</a>　<a href="./">趣味の始め方ガイド</a>　<a href="../privacy.html">プライバシーポリシー・免責事項</a></p>
</div>
<script src="../config.js"></script>
<script src="../data.js"></script>
<script src="../article.js"></script>
</body>
</html>
"""


def steps_html(h):
    rows = []
    for st in ("know", "try", "gear"):
        rows.append(
            f'<li><span class="st">{STEP_LABEL[st]}</span>'
            f'<span class="slot" data-hobby="{e(h["id"])}" data-step="{st}">{e(h["steps"][st])}</span></li>'
        )
    return '<ol class="steps">' + "".join(rows) + "</ol>"


def article_page(h, body_html, meta, data, site, related):
    t = data["types"][type_key(h)]
    url = f"{site}hobby/{h['id']}.html"
    title = f"{h['name']}の始め方｜費用・時間の目安と最初の3ステップ | シュミのたね"
    desc = f"{h['name']}を大人の初心者が始めるには？ {h['desc']} 初期費用・月額・週の時間の目安と、知る・試す・そろえるの3ステップで紹介します。"
    updated = meta.get("updated", datetime.date.today().isoformat())
    rel = "".join(
        f'<li><a href="{e(r["id"])}.html"><b>{e(r["name"])}の始め方</b><small>{e(r["desc"])}</small></a></li>' for r in related
    )
    return HEAD.format(title=e(title), desc=e(desc), url=e(url), site=e(site), og_type="article") + f"""  <nav class="crumbs" aria-label="パンくずリスト"><a href="../">トップ</a> › <a href="./">趣味の始め方ガイド</a> › {e(h['name'])}</nav>
  <main>
    <article class="card article">
      <span class="eyebrow">{e(h['category'])}</span>
      <h1>{e(h['name'])}の始め方</h1>
      <p class="lead">{e(h['desc'])}</p>
      <div class="meta"><span>初期費用 {yen(h['initial'])}〜</span><span>月 {yen(h['monthly'])}〜</span><span>週 {h['hours']}時間〜</span></div>
      <p class="policy">費用と時間は始めるときの目安です。地域・お店・やり方によって変わります。</p>
      <div class="fit-type"><span class="animal" aria-hidden="true">{t['animal']}</span><span>特に合いやすいタイプ<br><b>{e(t['name'])}</b>（{e(t['tagline'])}）</span></div>
{body_html}
      <h2>{e(h['name'])}を始める3ステップ</h2>
      {steps_html(h)}
      <p class="policy">リンクには広告（PR）を含むことがあります。紹介料の有無で、紹介する順番や内容は変えていません。</p>
      <div class="cta">
        <p><b>{e(h['name'])}は自分に合う？</b><br>14の質問で、あなたに合う趣味を3つ提案します（約2分・無料）。</p>
        <a class="btn" href="../#q" data-cta="diagnosis">自分に合うか診断する</a>
      </div>
      <p class="policy">最終更新日: {e(updated)}</p>
    </article>
    {f'<section class="card"><div class="section-title"><h3>近いタイプの趣味</h3></div><ul class="related">{rel}</ul></section>' if rel else ''}
  </main>
""" + FOOT


def index_page(articles, data, site):
    url = f"{site}hobby/"
    title = "趣味の始め方ガイド｜大人の初心者向けに費用・時間の目安を紹介 | シュミのたね"
    desc = "大人の初心者が新しい趣味を始めるためのガイド。趣味ごとに、費用・時間の目安と、知る・試す・そろえるの3ステップを紹介します。"
    cards = "".join(
        f'<li><a href="{e(h["id"])}.html"><b>{data["types"][type_key(h)]["animal"]} {e(h["name"])}の始め方</b>'
        f'<small>{e(h["desc"])}</small><small>初期費用 {yen(h["initial"])}〜・月 {yen(h["monthly"])}〜・週 {h["hours"]}時間〜</small></a></li>'
        for h in articles
    )
    return HEAD.format(title=e(title), desc=e(desc), url=e(url), site=e(site), og_type="website") + f"""  <nav class="crumbs" aria-label="パンくずリスト"><a href="../">トップ</a> › 趣味の始め方ガイド</nav>
  <main>
    <section class="card article">
      <h1>趣味の始め方ガイド</h1>
      <p class="lead">気になる趣味を、大人の初心者が始めるためのガイドです。費用と時間の目安、最初の3ステップを趣味ごとにまとめました。</p>
      <ul class="guide-list">{cards}</ul>
      <div class="cta">
        <p><b>どれが自分に合うかわからないときは</b><br>14の質問で、あなたに合う趣味を3つ提案します（約2分・無料）。</p>
        <a class="btn" href="../#q" data-cta="diagnosis">趣味診断をはじめる</a>
      </div>
    </section>
  </main>
""" + FOOT


def main():
    browser = find_browser()
    site = read_site_url()
    data = load_data(browser)
    by_id = {h["id"]: h for h in data["hobbies"]}
    files = sorted(CONTENT.glob("*.md"))
    if not files:
        sys.exit("content/hobbies/ に記事がありません。")

    articles, metas = [], {}
    for f in files:
        if f.stem not in by_id:
            sys.exit(f"{f.name}: data.js に趣味ID「{f.stem}」がありません。")
        articles.append(by_id[f.stem])
        metas[f.stem] = read_article(f)

    out_dir = SITE / "hobby"
    out_dir.mkdir(exist_ok=True)
    for old in out_dir.glob("*.html"):
        old.unlink()  # 記事を消したときに古いページが残らないようにする

    for h in articles:
        meta, body = metas[h["id"]]
        others = [a for a in articles if a["id"] != h["id"]]
        related = sorted(others, key=lambda a: distance(h, a, data["axes"]))[:3]
        page = article_page(h, md_to_html(body), meta, data, site, related)
        (out_dir / f"{h['id']}.html").write_text(page, encoding="utf-8", newline="\n")
        print(f"site/hobby/{h['id']}.html")

    (out_dir / "index.html").write_text(index_page(articles, data, site), encoding="utf-8", newline="\n")
    print("site/hobby/index.html")

    ids = json.dumps([h["id"] for h in articles])
    (SITE / "articles.js").write_text(
        "// tools/build_articles.py が生成するファイル。直接編集しない。\n"
        f"window.SHUMI_ARTICLES = {ids};\n", encoding="utf-8", newline="\n")
    print("site/articles.js")

    today = datetime.date.today().isoformat()
    urls = [(site, today), (f"{site}hobby/", today), (f"{site}privacy.html", today)]
    urls += [(f"{site}hobby/{h['id']}.html", metas[h["id"]][0].get("updated", today)) for h in articles]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{e(u)}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    sitemap += "</urlset>\n"
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8", newline="\n")
    print("site/sitemap.xml")


if __name__ == "__main__":
    main()
