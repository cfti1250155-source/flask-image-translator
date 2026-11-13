# AI Universal Translator

Flask製の翻訳アプリ（テキスト／画像／音声／カメラ／チャット）。翻訳は Gemini を使います。

## 環境変数（Render の Environment に設定）
| 名前 | 内容 |
|---|---|
| `GEMINI_API_KEY` | 必須。Gemini の API キー |
| `SECRET_KEY` | 必須（render.yaml なら自動生成）。未設定だと再起動のたびに表示言語の設定が消えます |
| `GEMINI_MODEL` | 任意。既定は `gemini-4-hydrogen`。**消えたモデル名を入れると 404 で全部失敗します。AI Studio の「Get code」にあるモデル名をコピーして貼ってください** |
| `GEMINI_FALLBACK_MODEL` | 任意。既定は `gemini-3.8-flash`。混雑(503)・時間切れ・モデルが無い(404)のとき、2回目の試行でこのモデルに切り替えます（空にすると切り替えません） |
| `GEMINI_THINKING_LEVEL` | 任意。既定は `low`。翻訳に長い「思考」は不要なので下げて速くします（`off` で指定なし、`GEMINI_THINKING=1` でモデルの既定に戻す） |
| `GEMINI_TIMEOUT` / `GEMINI_ATTEMPTS` | 任意。1回の待ち秒数（既定40）／一時的な失敗時の試行回数（既定2） |
| `RATE_PER_MIN` / `DAILY_LIMIT_PER_IP` / `SITE_DAILY_LIMIT` | 任意。1分・IP別1日・サイト全体1日の上限（既定 20 / 300 / 3000）。**無料枠の1日の上限は AI Studio の「レート制限」画面で確認し、`SITE_DAILY_LIMIT` をそれより少し低く設定してください**（上限に達したら Google 側が 429 を返し、画面には「利用が集中しています」と出ます） |
| `ADMIN_TOKEN` | 任意。設定すると `/api/stats?token=...` で日別の利用件数・エラー種別を確認できます |
| `KEEP_ALIVE_URL` | 任意。`https://自分のURL/healthz` を入れると10分ごとに自分を呼んでスリープを防ぎます（外部の監視サービスで /healthz を5分おきに呼ぶ方が確実） |

## 画面の多言語化
- 日本語・英語は `languages.py` に手書き。それ以外は `ui_labels/<言語コード>.json` を読みます。
- ファイルが無い言語は、スタート画面で選んだ時に Gemini が一度だけ自動翻訳して保存します（失敗したら英語で表示）。
  Render の無料枠はディスクが消えるため、**事前生成してコミット**しておくのがおすすめです。

```bash
export GEMINI_API_KEY=...
pip install -r requirements.txt
python tools/generate_ui_labels.py          # 未生成の言語だけ作る（--force で全作り直し）
git add ui_labels && git commit -m "Add UI labels"
```
生成された JSON は母語話者に確認してもらい、直接編集して構いません。`From` / `To` は全言語で固定です。

## AI学習（スラング・省略語への対応）
モデルの再学習ではなく、翻訳のたびに次を Gemini に渡して精度を上げています（すべて端末内に保存）。
- 直近のチャットの流れ（文脈）
- 用語集（履歴タブ → 用語集）
- 訳を直した内容（修正例。直近3件を手本として送信）

## Render の起動コマンド
サービスを Docker ではなく Python（Native）で作った場合は、Settings → Start Command を次にしてください（既定の `gunicorn app:app` は待ち時間が30秒で、Geminiが遅いとサーバーが落ちて「Internal Server Error」になります）。
```
gunicorn -w 1 --threads 8 --timeout 120 -b 0.0.0.0:$PORT app:app
```
（`Dockerfile` を使う場合は同じ内容がすでに入っています）

## ローカル起動
```bash
pip install -r requirements.txt
GEMINI_API_KEY=... FLASK_DEBUG=1 python app.py
```

## データの保存とバックアップ
履歴・お気に入り・用語集・単語帳・チャットは、各自のブラウザ（localStorage）にだけ保存されます。履歴タブ →「データ」で次の操作ができます。
- バックアップの書き出し（JSON。iPhoneは共有シートから「ファイルに保存」）／読み込み（今のデータに追加。重複はまとめます）
- 端末のデータと設定をすべて削除（ゴミ箱の中身も含めて完全に消えます。こちらは元に戻せません）
- ブラウザに保存データの永続化を依頼（Safariが長期間使われないサイトのデータを消すのを防ぐ。許可は端末次第）

## ゴミ箱（元に戻せる削除）
- 履歴・用語集・単語帳・チャットを消すと、すぐには消えず「ゴミ箱」（履歴タブ →「ゴミ箱」）に **30日間** 残ります。消した直後は画面下に［元に戻す］が出ます。
- ゴミ箱からは「元に戻す」「完全に削除」「ゴミ箱を空にする」ができます。30日たつと自動で消えます。
- ゴミ箱はこの端末の中だけ（バックアップの書き出しには含みません）。

## ホーム画面に追加（PWA）とオフライン
- iPhone: Safari で開き、共有ボタン →「ホーム画面に追加」。アプリのように全画面で起動します（履歴タブ →「データ」にも案内あり）。
- 通信できないときは、自動で「オフライン画面」（`/offline`）が開きます。履歴・お気に入り・用語集・フレーズ集・バックアップの書き出しが使えます。**翻訳そのものにはインターネットが必要です。**
- 画面の部品（JS/CSS/アイコン/フレーズ集）は Service Worker（`/sw.js`）が端末に保存します。デプロイして内容が変わると版番号が変わり、古い保存は自動で消えます。
- Tailwind・FontAwesome は外部CDNなので、**初回にオンラインで一度開いておく**と、以後オフラインでも見た目が崩れません。
- Service Worker は https（または localhost）でだけ動きます。

## フレーズ集（オフライン）
- 11カテゴリ・81文（あいさつ／**空港・飛行機の5カテゴリ45文**（チェックイン・保安検査と入国・搭乗口と乗り継ぎ・機内・到着と荷物）／食事・移動・買い物・宿泊・緊急）。人や場所の名前が入る文は入れず、固定の文だけです。手書きで17言語（日・英・中(簡/繁)・韓・西・仏・独・伊・葡・露・アラビア・ヒンディー・トルコ・インドネシア・タイ・ベトナム）。
- データは `tools/phrasebook_data.py`。直したら `python tools/build_phrasebook.py` で `static/phrasebook/*.json` に書き出します。
- 他の言語は `python tools/generate_phrasebook.py`（Gemini）で作れます（機械翻訳なので、できればネイティブの確認を）。
- 手書き分も、ネイティブの方に確認してもらうと安心です。

## テスト
```bash
pip install pytest playwright   # e2e を動かすときだけ playwright
python -m pytest tests -q       # サーバー側（Geminiはダミー）
python tests/e2e.py             # ブラウザ動作（Chromium）
python tests/e2e_backup.py      # バックアップ機能のブラウザ動作
python tests/e2e_pwa.py         # PWA・オフライン・フレーズ集のブラウザ動作
python tests/e2e_v11.py         # 結果カードの「…」メニュー・ゴミ箱・元に戻す（スマホ幅）
```
