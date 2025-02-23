現在はまだ npm run serve コマンドで Vuetify のサンプルコードが立ち上げあるだけの状態です。/workspace/backend/src/functions/ にある main.py の streamlit アプリを vue-advanced-chat を使って Vuetify アプリとして置き換えたいです。
vue-advanced-chat はインストール済みです。
/workspace/frontend/Vuetify にて`npm run serve`コマンドを私が実行中のため、リアルタイムに私は変更を確認できます。
/workspace/backend/src/functions/database.py も確認する必要があるでしょう。
チャットに参加しているメンバーを左側に一覧で表示し、LLM 及び他ユーザーとリアルタイムでやり取りする機能を実装したいです。/workspace/backend/src/functions/techbar サンプル.png に streamlit アプリ版の画像を保存してあります。
基本的には同じレイアウト、同じ機能にしてください。デバッグ欄は無くても良いです。
元の streamlit アプリは Fastapi サーバーにして、Vue のフロントエンドと同じコンテナ内で通信させる予定です。
