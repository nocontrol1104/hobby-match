# hobby-match

人と趣味をつなぎ、新しい趣味に出会えるマッチングサイト（仮称「シュミのたね」）の開発リポジトリです。

- まず「趣味診断」を公開し、結果ページの「始め方」からアフィリエイトで収益化します。
- ゆくゆくは、同じ趣味のユーザー同士がつながれる機能を追加します。

## 今の状態

仕様書 v0.2 に沿った趣味診断（5軸・14問・動物8タイプ・趣味41件）が `site/` で動きます。まだ公開はしていません。

| パス | 内容 |
|---|---|
| `site/` | 公開するサイト一式。ビルド不要の HTML / CSS / JS。 |
| `site/data.js` | 質問・タイプ・趣味マスタ・アフィリエイトリンクのデータ。 |
| `site/app.js` | 診断ロジックと画面。 |
| `site/config.js` | サイト名、GA4 の測定ID、事前登録・お問い合わせフォームの URL。 |
| `site/privacy.html` | プライバシーポリシー・免責事項。 |
| `docs/spec-hobby-diagnosis.md` | 趣味診断の仕様書 v0.2 の要点。 |
| `docs/deploy.md` | GitHub Pages での公開手順と計測イベント。 |
| `CLAUDE.md` | Claude Code で開発するときのルール。 |

## Ubuntu でのセットアップ

### 1. 必要なものを入れる

```bash
sudo apt update
sudo apt install -y git python3
```

### 2. リポジトリを clone する

非公開リポジトリなので、GitHub の認証が必要です。GitHub CLI を使う方法が簡単です。

```bash
sudo apt install -y gh
gh auth login          # GitHub.com → HTTPS → ブラウザでログイン
gh repo clone nocontrol1104/hobby-match
cd hobby-match
```

SSH 鍵を GitHub に登録済みなら `git clone git@github.com:nocontrol1104/hobby-match.git` でも構いません。

### 3. 診断を動かす

ファイルを直接開くだけでも動きます。

```bash
xdg-open site/index.html
```

スマホなど同じ Wi-Fi の別の端末から見たいときは、簡易サーバーを立てます。

```bash
python3 -m http.server 8000 --directory site
# ブラウザで http://localhost:8000/ を開く
```

診断結果は URL（`#r=...`）とブラウザの localStorage にだけ入り、サーバーには送りません。

### 4. Claude Code を使う（任意）

Node.js 18 以上が必要です。

```bash
npm install -g @anthropic-ai/claude-code
cd hobby-match
claude
```

起動すると `CLAUDE.md` のルールが自動で読み込まれます。

## 開発の流れ

1. `main` から作業ブランチを切る（例: `feature/diagnosis-logic`）。
2. 変更をコミットして push し、Pull Request を作る。
3. レビューしてから `main` にマージする。

詳しいルールは [`CLAUDE.md`](CLAUDE.md) を参照してください。

## 公開

GitHub Pages（無料）で公開する予定です。手順は [`docs/deploy.md`](docs/deploy.md) にあります。
無料プランの GitHub Pages は公開リポジトリでしか使えないため、公開の前にリポジトリを公開にするかどうかを決める必要があります。

## 今後の予定

1. 公開方法を決めて、GA4 の測定IDと事前登録フォームを設定し、MVP を公開する。
2. タイプごとのシェア用 OGP 画像と動物イラストを用意する（今は絵文字で代用）。
3. ASP に登録し、審査に通った案件を `site/data.js` の `links` に入れる。
4. 趣味詳細ページを記事化して検索流入を狙う（段階2）。
5. 会員・交流機能は Supabase の無料枠で作る（段階3〜）。

## ライセンス

未定です。決まるまでは無断での利用・再配布はできません。
