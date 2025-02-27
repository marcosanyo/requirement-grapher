## 前置き

今回は「要件・制約分析支援システム」についてご紹介します。このアプリは、テキスト入力から要件と制約を自動的に抽出し、それらの関係性をグラフとしてかっこよく可視化するツール・・・の検証です。
[AI Agent Hackathon with Google Cloud](https://zenn.dev/hackathons/2024-google-cloud-japan-ai-hackathon) に参加した際のアカウントとクレジットが余っているのでやってみました。
コード自体もGeminiなどを活用しています。

## 🌟 アプリの概要

「あぁ、またミーティングで要件が増えた...どれがどう関連してるんだっけ？」
「この制約とあの要件って矛盾してない？」

こんな悩みを解決するために生まれたのが、この「要件・制約分析支援システム」です。テキストを入力するだけで、AI（Gemini）が自動的に以下の要素を抽出してくれます：

- 要件 (Requirements)
- 制約 (Constraints)
- 暗黙知/前提 (Implicit Knowledge)

そして、それらの関係性をインタラクティブなグラフとして表示します。
直でグラフ用コードを作成しようとすると安定しませんが、中間表現としてYAMLを用いることで関係性リンクが安定して生成されるようになります。

## 💡 主な機能

1. **テキストからの自動抽出**: 仕様書や会議のメモをコピペするだけ
2. **YAML中間形式**: 抽出結果をYAML形式で確認可能
3. **インタラクティブなグラフ表示**: D3.jsによる美しい可視化
4. **グラフ操作機能**: マウス操作で視点を動かせる

## 🎬 動作
1. テキストを入力欄に貼り付ける
2. 「分析開始」ボタンをクリック
3. AIが要件・制約を抽出してYAML形式で表示
4. グラフが自動的に生成される
5. グラフをドラッグやホイールで操作

### 例
#### 要件例1
それっぽい要件をLLMに作ってもらいました
   ```
教育現場のデジタル化に対応するため、新しいオンライン学習プラットフォームの開発を計画しています。この学習システムでは、教師が教材を提供し、学生が自分のペースで学習を進められることが重要です。
教師側としては、授業コンテンツの作成と管理が容易であることが求められています。特に、様々な形式の教材をアップロードでき、課題の設定や学生の進捗確認ができる機能が必要です。
学生側では、自分に合ったコースを見つけて登録し、提供された教材で学習した後、理解度を確認するためのテストに取り組めるようにしたいと考えています。また、疑問点があれば教師に質問できる仕組みも欲しいです。
システムの利用者数は最大でも1000人程度を想定していますが、特に学期開始時には同時アクセスが集中するかもしれません。また、モバイル端末からのアクセスも多いため、スマートフォンでの使いやすさも意識する必要があります。
プライバシーへの配慮も欠かせません。学生の個人情報や成績データは適切に保護されるべきです。
プロジェクトの予算は限られており、開発期間は3ヶ月程度を予定しています。まずは基本機能を実装し、その後必要に応じて機能を拡張していく方針です。
   ```
沢山ノードが表示されてそれっぽい
![](https://storage.googleapis.com/zenn-user-upload/31d3219eceed-20250228.gif)
#### 要件例2
雑な要件でも抽出してくれます。
```
かっこいいUIを作る
```
良い感じ・・・だけどなんで回転するんだ？
![](https://storage.googleapis.com/zenn-user-upload/c3b912b7af04-20250228.gif)

## 🔧 技術スタック

このアプリは以下の技術で構築されています：

### フロントエンド
- Vue.js 3 (Composition API)
- Vuetify
- D3.js
- Pinia (状態管理)

### バックエンド
- FastAPI
- Google Gemini API

### インフラ
- Google Cloud
  - Cloud Run

## 🚀 今後の展望

今後は(できれば)以下の機能を追加したいです

1. 今回作成したVueフロントエンドに限らない形式での提供
2. PDFやPNG形式での出力
3. 矢印や文字表記など見た目の調整
4. ハリボテ箇所をどうにかする

## 📌 最後に
今回のアプリはあくまで検証用のため、今後あまり改善はされないかもしれません。

要件分析、もっと楽しくなるかも？
そんな希望を込めて、今日も開発を続けています。
