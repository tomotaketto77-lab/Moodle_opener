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



## アプリ化（実行可能ファイルの作成）

このアプリケーションは、PyInstallerを使用することで、Pythonがインストールされていない環境でも実行可能なファイル（.exeなど）に変換することができます。

1.  **PyInstallerをインストールします**
    ```bash
    pip install pyinstaller
    ```

2.  **実行可能ファイルを作成します**

    プロジェクトのルートディレクトリ（`app.py`がある場所）で、以下のコマンドを実行します。
    ```bash
    pyinstaller app.py --onefile --add-data "templates:templates" --add-data "static:static"
    ```
    これにより、`dist`というフォルダの中に実行可能ファイル（Windowsの場合は `app.exe`）が作成されます。

3.  **実行します**

    `dist`フォルダ内に作成された実行可能ファイルを実行します。

    **注意:** アプリケーションを正常に動作させるためには、作成された実行可能ファイルと同じディレクトリに、**Google Chrome Driver**（`chromedriver.exe`など）を配置する必要があります。
