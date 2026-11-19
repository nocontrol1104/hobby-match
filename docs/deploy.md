# 公開手順（GitHub Pages、無料）

`site/` フォルダがそのままサイトになります。ビルドは不要です。
公開すると URL は `https://nocontrol1104.github.io/hobby-match/` になります。

> **まだ公開していません。** 下の「最初に決めること」が決まってから進めます。

## 最初に決めること（費用に関わる）

GitHub Pages は、**無料プランでは公開（Public）リポジトリでしか使えません**。
今のリポジトリは非公開（Private）なので、次のどちらかを選ぶ必要があります。

| 方法 | 費用 | 変わること |
|---|---|---|
| A. リポジトリを公開にして GitHub Pages を使う（おすすめ） | 無料 | コードと資料（`docs/` を含む）が誰でも見られるようになる。秘密情報は元々置かないルールなので問題は少ない。 |
| B. 非公開のまま Cloudflare Pages など別の無料サービスを使う | 無料 | Cloudflare のアカウント作成が必要。URL は `○○.pages.dev` になる。 |
| C. GitHub Pro にして非公開のまま GitHub Pages を使う | 有料（月額） | 費用がかかるため、選ぶ場合は事前に承認をもらう。 |

A を選ぶ場合、公開前に `docs/` に載せたくない内容がないか確認してください（収益試算やリサーチの要点が誰でも読めるようになります）。

## A の手順（リポジトリを公開して GitHub Pages）

1. GitHub でリポジトリを開き、**Settings → General** の一番下「Danger Zone」で **Change visibility → Public** にする。
2. **Settings → Pages** を開き、「Build and deployment」の **Source** を **GitHub Actions** にする。
3. **Actions** タブ →「GitHub Pages に公開」→ **Run workflow** を押す。
4. 1〜2分で `https://nocontrol1104.github.io/hobby-match/` が見られるようになる。
5. 以後は自動で公開したい場合、`.github/workflows/pages.yml` の `push:` の3行のコメントを外して main にマージする。

## 公開前にやること

- [x] `site/config.js` の `gaMeasurementId` に GA4 の測定ID（`G-` で始まる）を入れる。GA4 は無料。
  - <https://analytics.google.com/> でプロパティを作成 → 「ウェブ」のデータストリームを追加 → URL に公開先を入れる → 表示された測定IDをコピー。
- [ ] 「同じタイプの人とつながる」の事前登録用に Google フォーム（無料）を作り、URL を `site/config.js` の `signupFormUrl` に入れる。
- [x] プライバシーポリシー（GA4 を使うことの記載が必要）を用意する → `site/privacy.html`
- [x] お問い合わせ用に Google フォーム（無料）を作り、URL を `site/config.js` の `contactFormUrl` に入れる。
- [ ] アフィリエイトの審査に通ったら、`site/data.js` の `links` にリンクを追加する。

## 計測しているイベント（GA4）

| イベント名 | いつ | 主なパラメータ |
|---|---|---|
| `diagnosis_start` | 診断を始めたとき | なし |
| `diagnosis_complete` | 14問に答え終えたとき | `type`（例: `HLH`）, `question_version` |
| `affiliate_click` | 始め方のリンクを押したとき | `hobby_id`, `step`（know/try/gear）, `rank`（記事ページは 0）, `partner`, `page`（記事ページは `article`） |
| `article_cta_click` | 記事ページの「診断する」ボタンを押したとき | `cta`, `page`（ページのパス） |
| `share` | X / LINE のシェアを押したとき | `method`, `type` |
| `signup_click` | 事前登録ボタンを押したとき | `type` |

診断完了率は `diagnosis_complete ÷ diagnosis_start` で出せます。

## 手元で確認する

```bash
cd hobby-match
xdg-open site/index.html                         # そのまま開く
python3 -m http.server 8000 --directory site     # または http://localhost:8000/
```
