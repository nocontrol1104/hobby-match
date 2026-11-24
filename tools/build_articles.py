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
  site/index.html の STATIC 部分 JS を読まない AI・クローラ向けのトップの本文
  site/about.html               このサイトについて・診断の仕組み

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

FOOT = """  <p class="foot"><a href="../">趣味診断</a>　<a href="./">趣味の始め方ガイド</a>　<a href="../about.html">このサイトについて</a>　<a href="../privacy.html">プライバシーポリシー・免責事項</a></p>
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


# ---------- トップの静的な本文 と 「このサイトについて」ページ ----------
# トップ（index.html）は JS で画面を描くため、JS を読まない AI・クローラには中身が見えない。
# そこで data.js から作った本文を index.html の STATIC:START〜END の間に入れておく。
# JS が動くと app.js が #view の中身を差し替えるので、ふつうの利用者には今までどおりの画面が出る。

STATIC_START = "<!-- STATIC:START"
STATIC_END = "<!-- STATIC:END -->"


def read_contact_url():
    m = re.search(r'contactFormUrl:\s*"([^"]*)"', (SITE / "config.js").read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def pole_names(data, key):
    return " × ".join(data["axes"][i]["high" if c == "H" else "low"] for i, c in enumerate(key))


def types_html(data):
    cards = "".join(
        f'<div class="type-card"><span class="animal" aria-hidden="true">{t["animal"]}</span>'
        f'<b>{e(t["name"])}</b><span>{e(pole_names(data, k))}</span><span>{e(t["text"])}</span></div>'
        for k, t in data["types"].items()
    )
    return f'<div class="type-grid">{cards}</div>'


def hobby_index_html(data, article_ids):
    rows = []
    for h in data["hobbies"]:
        name = e(h["name"])
        if h["id"] in article_ids:
            name = f'<a href="hobby/{e(h["id"])}.html">{name}</a>'
        rows.append(f'<li><b>{name}</b>（{e(h["category"])}）— {e(h["desc"])}</li>')
    return '<ul class="hobby-index">' + "".join(rows) + "</ul>"


def static_top_html(data, article_ids):
    n = len(data["hobbies"])
    axes = "".join(f'<li><b>{e(a["name"])}</b>：{e(a["low"])} ↔ {e(a["high"])}</li>' for a in data["axes"])
    return f"""{STATIC_START} tools/build_articles.py が生成。直接編集しない。JS が動くと app.js がこの中身を差し替える。 -->
    <section class="card hero">
      <h1>14の質問で、<br><em>あなたに合う趣味</em>が見つかる。</h1>
      <p class="lead">シュミのたねは、20〜40代の社会人向けの無料の趣味診断です。14の質問（約2分）に答えると、あなたを8種類の動物タイプにたとえて、{n}種類の趣味から合うものを3つと、ちょっと意外な出会いをひとつ提案します。</p>
      <noscript><p class="policy">診断を受けるには、ブラウザの JavaScript を有効にしてください。</p></noscript>
      <p><a href="hobby/">趣味の始め方ガイド</a>・<a href="about.html">このサイトについて・診断の仕組み</a></p>
    </section>
    <section class="card">
      <h2>診断のしくみ</h2>
      <p>12の質問から、趣味の好みを5つの軸（0〜100）で表します。残りの2問で、趣味に使える月の予算と週の時間を聞きます。</p>
      <ul>{axes}</ul>
      <p>「場所」「人数」「活動量」の3つの軸で8つの動物タイプが決まり、5つの軸の近さ（合い度）と予算・時間の条件から、おすすめの趣味を選びます。おすすめの順位は、広告の紹介料では変えていません。くわしくは<a href="about.html">診断の仕組み</a>をご覧ください。</p>
    </section>
    <section class="card">
      <h2>8つの動物タイプ</h2>
      {types_html(data)}
    </section>
    <section class="card">
      <h2>診断で提案する趣味（{n}種類）</h2>
      <p>リンクのある趣味は、始め方ガイド（費用・時間の目安と最初の3ステップ）を読めます。</p>
      {hobby_index_html(data, article_ids)}
    </section>
    {STATIC_END}"""


def inject_static_top(data, article_ids):
    p = SITE / "index.html"
    s = p.read_text(encoding="utf-8")
    i, j = s.find(STATIC_START), s.find(STATIC_END)
    if i < 0 or j < 0:
        sys.exit("site/index.html に STATIC:START / STATIC:END の目印がありません。")
    s = s[:i] + static_top_html(data, article_ids) + s[j + len(STATIC_END):]
    p.write_text(s, encoding="utf-8", newline="\n")


# 記事用の HEAD / FOOT を、サイト直下のページ用にパスを直して使う
ABOUT_HEAD = HEAD.replace('href="../style.css"', 'href="style.css"').replace('href="../"', 'href="./"')
ABOUT_FOOT = (FOOT.replace('<a href="../">趣味診断</a>', '<a href="./">趣味診断</a>')
              .replace('<a href="./">趣味の始め方ガイド</a>', '<a href="hobby/">趣味の始め方ガイド</a>')
              .replace('href="../about.html"', 'href="about.html"')
              .replace('href="../privacy.html"', 'href="privacy.html"')
              .replace('src="../', 'src="'))


def about_page(data, site):
    n = len(data["hobbies"])
    axis = {a["id"]: a for a in data["axes"]}
    contact = read_contact_url()
    contact_html = (f'<a href="{e(contact)}" target="_blank" rel="noopener">お問い合わせフォーム</a>'
                    if contact.startswith("https://") else "準備中")
    qs = "".join(
        f'<li>{e(q["text"])}（{e(axis[q["axis"]]["name"])}：'
        f'{e(axis[q["axis"]]["high" if q["dir"] == "high" else "low"])}の向き）</li>'
        for q in data["questions"]
    )
    conds = "".join(
        f'<li>{e(c["text"])}（{e(" / ".join(o["label"] for o in c["options"]))}）</li>' for c in data["conditions"]
    )
    weights = "、".join(f'{e(a["name"])} {a["weight"]}' for a in data["axes"])
    title = "このサイトについて・診断の仕組み | シュミのたね"
    desc = "趣味診断サイト「シュミのたね」の運営者、目的、診断の仕組み（5つの軸、8つの動物タイプ、合い度の計算）、広告の方針を説明します。"
    head = ABOUT_HEAD.format(title=e(title), desc=e(desc), url=e(f"{site}about.html"), site=e(site), og_type="website")
    return head + f"""  <nav class="crumbs" aria-label="パンくずリスト"><a href="./">トップ</a> › このサイトについて</nav>
  <main>
    <article class="card article">
      <h1>このサイトについて・診断の仕組み</h1>
      <h2>シュミのたねとは</h2>
      <p>シュミのたねは、20〜40代の社会人が新しい趣味に出会うための無料の趣味診断サイトです。14の質問に答えると、好みの傾向を8種類の動物タイプにたとえ、{n}種類の趣味から合うものを提案します。趣味ごとの<a href="hobby/">始め方ガイド</a>では、費用と時間の目安と、知る・試す・そろえるの3ステップで始め方を紹介しています。</p>
      <p>ゆくゆくは、同じ趣味の人同士がつながれる機能を加える予定です（準備中）。</p>
      <h2>運営者</h2>
      <ul>
        <li>運営者：シュミのたね運営事務局</li>
        <li>公開日：2026年11月19日</li>
        <li>お問い合わせ：{contact_html}</li>
      </ul>
      <h2>診断の仕組み</h2>
      <h3>1. 質問（14問）</h3>
      <p>12問は「とてもそう思う」〜「まったくそう思わない」の5段階で答えます。</p>
      <ol>{qs}</ol>
      <p>残りの2問は、おすすめを絞り込むための条件です。</p>
      <ul>{conds}</ul>
      <h3>2. 5つの軸のスコア</h3>
      <p>5段階の回答を +2〜−2 の点にし、軸ごとに合計して 0〜100 に直します。100 に近いほど、その軸の右側（屋外、みんな、アクティブ、つくる、本格的に）の傾向が強いことを表します。</p>
      <h3>3. 8つの動物タイプ</h3>
      <p>「場所」「人数」「活動量」の3つの軸が 50 以上か未満かで、8つのタイプに分けます。</p>
      {types_html(data)}
      <h3>4. おすすめの趣味の選び方</h3>
      <ul>
        <li>趣味ごとに、5つの軸の値（0〜100）を決めてあります。あなたのスコアとの近さ（重み付きの距離）から「合い度」を計算します。重みは {weights} です。</li>
        <li>月の予算と週の時間の条件を超える趣味は、候補から外します。外すと候補が少なくなりすぎる場合は外さずに、超えた段階の数に応じて合い度を下げます。</li>
        <li>合い度の高い順に、同じジャンルの趣味は1つまでにして3つを選びます。</li>
        <li>4位以降から、3つの軸のうち1つだけ傾向が違う趣味を「意外な出会い」として1つ紹介します。</li>
      </ul>
      <p class="policy">診断は趣味を見つけるきっかけとしての目安です。趣味の軸の値は運営者が設定したもので、今後の利用状況を見て調整します。</p>
      <h2>広告とおすすめの方針</h2>
      <ul>
        <li>本サイトはアフィリエイト広告を利用しています。広告のリンクには「PR」と表示します。</li>
        <li><b>診断のおすすめの順位は、診断の計算だけで決めています。</b>紹介料の有無や金額で、順位や内容を変えることはありません。</li>
        <li>診断の回答は、お使いのブラウザの中にだけ保存されます。くわしくは<a href="privacy.html">プライバシーポリシー</a>をご覧ください。</li>
      </ul>
      <h2>始め方ガイドの書き方</h2>
      <ul>
        <li>大人の初心者が最初の一歩を踏み出せるよう、魅力、費用と時間の考え方、つまずきやすいポイント、よくある質問をまとめています。</li>
        <li>費用と時間は始めるときの一般的な目安です。地域・お店・やり方によって変わります。</li>
        <li>確かめられない料金や効果は書かないようにしています。健康や安全に関わる内容では、医師や専門家への相談をおすすめしています。</li>
      </ul>
    </article>
  </main>
""" + ABOUT_FOOT



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

    article_ids = {h["id"] for h in articles}
    inject_static_top(data, article_ids)
    print("site/index.html（静的な本文）")
    (SITE / "about.html").write_text(about_page(data, site), encoding="utf-8", newline="\n")
    print("site/about.html")

    today = datetime.date.today().isoformat()
    urls = [(site, today), (f"{site}hobby/", today), (f"{site}about.html", today), (f"{site}privacy.html", today)]
    urls += [(f"{site}hobby/{h['id']}.html", metas[h["id"]][0].get("updated", today)) for h in articles]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{e(u)}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls)
    sitemap += "</urlset>\n"
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8", newline="\n")
    print("site/sitemap.xml")


if __name__ == "__main__":
    main()
