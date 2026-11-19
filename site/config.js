/*
 * サイト設定。公開前に値を入れる。空のままなら該当機能は無効になる。
 * ここに秘密情報は書かない（このファイルは公開される）。
 */
window.SHUMI_CONFIG = {
  siteName: "シュミのたね",
  // 公開先の URL（末尾は /）。シェア用画像・ページの絶対 URL に使う。変えたら tools/build_ogp.py を実行し直す。
  siteUrl: "https://nocontrol1104.github.io/hobby-match/",
  // GA4 の測定ID（例: "G-XXXXXXXXXX"）。空なら計測しない。
  gaMeasurementId: "G-S95NDLBWDQ",
  // 「同じタイプの人とつながる」事前登録用の Google フォームの URL。空なら準備中表示のみ。
  signupFormUrl: "",
  // お問い合わせ用の Google フォームの URL（https:// で始まるもの）。空なら「準備中」と表示する。
  contactFormUrl: "https://docs.google.com/forms/d/e/1FAIpQLScuTXyWn3Mdo0YMc45mp8l7gaqLQjBs1KQXpBjdc4b0nGsdnA/viewform",
};
