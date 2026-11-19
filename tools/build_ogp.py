"""
シェア用の画像とページを作るスクリプト。

  python tools/build_ogp.py

作るもの:
  site/ogp/default.png      サイト共通の画像（1200×630）
  site/ogp/<KEY>.png        8タイプ別の画像
  site/share/<KEY>.html     タイプ別のシェア用ページ（OGP を持ち、開くと結果ページへ移動する）

X や LINE は URL の # 以降を読まないため、タイプ別の画像を出すにはタイプごとのページが必要。
タイプ名・タグライン（site/data.js）やサイトの URL（site/config.js の siteUrl）を変えたら実行し直す。

画像は Chrome / Edge のヘッドレスモードでテンプレート（tools/ogp/template.html）を撮影して作る。
ブラウザが見つからないときは、環境変数 BROWSER に実行ファイルのパスを入れる。
外部ライブラリは使わない（Python 3.8 以上の標準ライブラリだけ）。
"""
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
TEMPLATE = ROOT / "tools" / "ogp" / "template.html"
WIDTH, HEIGHT = 1200, 630

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser():
    env = os.environ.get("BROWSER")
    if env:
        return env
    for c in BROWSER_CANDIDATES:
        if Path(c).is_file() or shutil.which(c):
            return c
    sys.exit("Chrome / Edge が見つかりません。環境変数 BROWSER にパスを入れてください。")


def read_site_url():
    text = (SITE / "config.js").read_text(encoding="utf-8")
    m = re.search(r'siteUrl:\s*"([^"]+)"', text)
    if not m:
        sys.exit("site/config.js に siteUrl がありません。")
    url = m.group(1)
    return url if url.endswith("/") else url + "/"


def read_types():
    """site/data.js の types から、キー・名前・タグラインを取り出す。"""
    text = (SITE / "data.js").read_text(encoding="utf-8")
    block = text[text.index("types: {"):]
    pattern = re.compile(r'([LH]{3}):\s*\{\s*animal:\s*"[^"]*",\s*name:\s*"([^"]+)",\s*tagline:\s*"([^"]+)"')
    types = {k: {"name": n, "tagline": t} for k, n, t in pattern.findall(block)}
    if len(types) != 8:
        sys.exit(f"data.js から8タイプを読み取れませんでした（{len(types)}件）。")
    return types


def screenshot(browser, url, out):
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([
            browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1", f"--user-data-dir={profile}",
            f"--window-size={WIDTH},{HEIGHT}", "--virtual-time-budget=8000",
            f"--screenshot={out}", url,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not Path(out).is_file():
        sys.exit(f"画像を作れませんでした: {out}")


SHARE_PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- tools/build_ogp.py が生成するファイル。直接編集しない。 -->
<title>{name} | シュミのたね</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{site}">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="シュミのたね">
<meta property="og:title" content="わたしの趣味タイプは「{name}」">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}share/{key}.html">
<meta property="og:image" content="{site}ogp/{key}.png">
<meta property="og:image:width" content="{w}">
<meta property="og:image:height" content="{h}">
<meta property="og:image:alt" content="趣味タイプ「{name}」">
<meta name="twitter:card" content="summary_large_image">
<script>location.replace("../" + location.hash);</script>
</head>
<body>
<p><a href="../">シュミのたねで趣味診断をする</a></p>
</body>
</html>
"""


def main():
    browser = find_browser()
    site_url = read_site_url()
    types = read_types()
    (SITE / "ogp").mkdir(exist_ok=True)
    (SITE / "share").mkdir(exist_ok=True)
    template_url = TEMPLATE.as_uri()

    screenshot(browser, template_url, SITE / "ogp" / "default.png")
    print("site/ogp/default.png")
    for key, t in types.items():
        screenshot(browser, f"{template_url}?key={key}", SITE / "ogp" / f"{key}.png")
        desc = f"{t['tagline']}。14の質問で、あなたに合う趣味が見つかる無料の趣味診断。"
        page = SHARE_PAGE.format(
            key=key, site=html.escape(site_url), name=html.escape(t["name"]),
            desc=html.escape(desc), w=WIDTH, h=HEIGHT,
        )
        (SITE / "share" / f"{key}.html").write_text(page, encoding="utf-8", newline="\n")
        print(f"site/ogp/{key}.png, site/share/{key}.html")


if __name__ == "__main__":
    main()
