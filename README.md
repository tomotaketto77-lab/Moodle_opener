# Moodle自動授業オープナー

指定した時間割に基づいて、自動でMoodleにログインし、該当する授業ページを開くためのFlaskアプリケーションです。

## 機能

- 曜日と時限に基づいた時間割設定
- 授業時間の設定
- Moodleのユーザー名とパスワードの保存
- 指定時刻になると自動でSelenium（Chrome）を起動し、授業ページを開く

## 必要なもの

- Python 3.x
- Google Chrome
- Google Chrome Driver
  - **注意:** お使いのChromeのバージョンに合ったChromeDriverをインストールし、システムのパスが通った場所に配置してください。

## インストールと実行方法

1. **リポジトリをクローンします**
   ```bash
   git clone https://github.com/tomotaketto77-lab/Moodle_opener.git
   cd Moodle_opener
   ```

2. **必要なライブラリをインストールします**
   ```bash
   pip install -r requirements.txt
   ```

3. **アプリケーションを実行します**
   ```bash
   python app.py
   ```

4. アプリケーションが起動すると、自動的にブラウザで `http://127.0.0.1:5000/` が開きます。画面の指示に従って時間割やMoodleの情報を設定してください。