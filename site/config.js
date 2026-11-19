/*
 * サイト設定。公開前に値を入れる。空のままなら該当機能は無効になる。
 * ここに秘密情報は書かない（このファイルは公開される）。
 */
window.SHUMI_CONFIG = {
  siteName: "シュミのたね",
  // GA4 の測定ID（例: "G-XXXXXXXXXX"）。空なら計測しない。
  gaMeasurementId: "",
  // 「同じタイプの人とつながる」事前登録用の Google フォームの URL。空なら準備中表示のみ。
  signupFormUrl: "",
  // お問い合わせ用の Google フォームの URL（https:// で始まるもの）。空なら「準備中」と表示する。
  contactFormUrl: "",
};
