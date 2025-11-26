from flask import Flask, request, render_template, redirect, url_for
import json, os, subprocess, webbrowser, sys
from threading import Timer
import time
from datetime import datetime
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# PyInstallerで実行された場合にリソースへのパスを解決する
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# テンプレートフォルダのパスを指定してFlaskアプリを初期化
app = Flask(__name__, template_folder=resource_path('templates'))

# 設定ファイル
# 実行ファイルと同じディレクトリにsettings.jsonを保存するようにする
# PyInstallerで --onefile を使う場合、sys.executableは実行ファイルのパスを指す
basedir = os.path.dirname(sys.executable) if hasattr(sys, 'frozen') else os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(basedir, "settings.json")
LOG_FILE = os.path.join(basedir, "worker_log.txt")
MOODLE_LOGIN_URL = "https://cms.aitech.ac.jp/login/index.php" # ログインページへの直接URL
MOODLE_COURSES_URL = "https://cms.aitech.ac.jp/my/courses.php" # コース一覧ページ

# -----------------------------
# 設定読み込み
# -----------------------------
def load_settings_for_flask():
    if not os.path.exists(SETTINGS_FILE):
        return {"period_times": [], "timetable": [], "moodle_username": "", "moodle_password": ""}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"period_times": [], "timetable": [], "moodle_username": "", "moodle_password": ""}

# -----------------------------
# 6限固定、空欄でも保持
# -----------------------------
def ensure_six_periods(settings):
    period_times = settings.get("period_times", [])
    if not period_times:
        period_times = [{"period": i, "start": "", "end": ""} for i in range(1,7)]
    else:
        for i in range(1,7):
            if not any(p["period"] == i for p in period_times):
                period_times.append({"period": i, "start": "", "end": ""})
    settings["period_times"] = sorted(period_times, key=lambda x: x["period"])
    return settings

settings = load_settings_for_flask()
settings = ensure_six_periods(settings)

# -----------------------------
# メイン画面
# -----------------------------
@app.route("/", methods=["GET","POST"])
def index():
    global settings
    if request.method == "POST":
        # Moodle情報
        settings["moodle_username"] = request.form.get("moodle_username", "")
        settings["moodle_password"] = request.form.get("moodle_password", "")

        # period_times（空欄も保持）
        period_numbers = sorted([int(k.replace("period_start_","")) for k in request.form.keys() if k.startswith("period_start_")])
        period_times = []
        for num in period_numbers:
            start = request.form.get(f"period_start_{num}", "").strip()
            end   = request.form.get(f"period_end_{num}", "").strip()
            period_times.append({"period": num, "start": start, "end": end})

        # 6限固定
        settings["period_times"] = ensure_six_periods({"period_times": period_times})["period_times"]

        # timetable
        timetable = []
        weekdays = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
        for p in settings["period_times"]:
            for day in weekdays:
                key = f"subject_{day}_{p['period']}"
                subject = request.form.get(key, "").strip()
                if subject:
                    timetable.append({"day": day, "period": p["period"], "subject": subject})

        day_order = {day:i for i,day in enumerate(weekdays)}
        settings["timetable"] = sorted(timetable, key=lambda x:(day_order[x["day"]], x["period"]))

        # 保存
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

        return redirect(url_for("index"))

    return render_template("index.html", settings=settings)

# -----------------------------
# worker.py 起動
# -----------------------------
@app.route("/run_worker", methods=["POST"])
def run_worker():
    try:
        # 自分自身を --worker 引数付きで起動する
        subprocess.Popen([sys.executable, "--worker"])
    except Exception as e:
        print("worker起動エラー:", e)
    return redirect(url_for("index"))

# -----------------------------
# 自動ブラウザ起動（タブ2つ防止）
# -----------------------------
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

# アプリ終了用ルート
# -----------------------------
@app.route("/shutdown", methods=["POST"])
def shutdown():
    """アプリを終了する"""
    log_message("シャットダウンリクエストを受け取りました。アプリを終了します。")
    os.kill(os.getpid(), 9) # 自分自身のプロセスを終了する
    return "Server is shutting down..." # このレスポンスは返されない

# --------------------------------------------------------------------
# ここから下は worker.py から持ってきたコード
# --------------------------------------------------------------------

def log_message(message):
    """ログファイルにメッセージを書き込む"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def load_settings_for_worker():
    """設定ファイルを読み込む"""
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_current_subject():
    """現在の曜日・時間から対象授業を取得"""
    settings = load_settings_for_worker()
    timetable = settings.get("timetable", [])
    period_times = settings.get("period_times", [])

    now = datetime.now()
    weekday = now.strftime("%A")  # Monday, Tuesday, ...
    current_time = now.strftime("%H:%M")

    current_period = None
    for pt in period_times:
        start = pt.get("start")
        end = pt.get("end")
        if start and end and start <= current_time <= end:
            current_period = pt["period"]
            break

    if current_period is None:
        return None

    for tt in timetable:
        if tt["day"] == weekday and tt["period"] == current_period:
            return tt["subject"]

    return None

def open_subject_with_selenium():
    from selenium.common.exceptions import StaleElementReferenceException
    """Moodleにログインして現在時刻の授業を開く"""
    log_message("ワーカープロセスを開始します。")
    try:
        settings = load_settings_for_worker()
        moodle_username = settings.get("moodle_username")
        moodle_password = settings.get("moodle_password")

        subject = get_current_subject()
        if subject is None:
            log_message("現在時刻に該当する授業はありません。処理を終了します。")
            return

        log_message(f"本日の授業: {subject}")

        log_message("Selenium (Chrome) を起動します...")
        opts = webdriver.ChromeOptions()
        # opts.add_argument("--headless=new") # 非表示にする場合は有効
        driver = webdriver.Chrome(options=opts)

        # --- ログイン処理 ---
        # StaleElementReferenceException対策として、最大3回まで再試行する
        login_attempts = 0
        while login_attempts < 3:
            try:
                driver.get(MOODLE_LOGIN_URL) # 毎回ログインページを再読み込み
                log_message(f"ログイン試行 {login_attempts + 1}回目...")
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "username"))).send_keys(moodle_username)
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(moodle_password)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "loginbtn"))).click()
                break # 成功したらループを抜ける
            except StaleElementReferenceException:
                login_attempts += 1
                log_message(f"StaleElementReferenceExceptionが発生しました。リトライします... ({login_attempts}/3)")
                if login_attempts >= 3:
                    log_message("ログイン試行が3回失敗しました。")
                    raise # エラーを再送出して処理を終了


        # ログインが完了し、ダッシュボードに遷移するまで待機
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "page-my-index")))
        log_message("Moodle にログインしました")

        # --- 授業ページへの移動 ---
        driver.get(MOODLE_COURSES_URL) # コース一覧ページに移動
        log_message("コース一覧ページに移動します。")

        # 授業名（部分一致）のリンクが表示され、クリック可能になるまで待つ
        link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, subject))
        )
        href = link.get_attribute("href")
        log_message(f"授業ページ発見 → {href}")
        link.click() # hrefを取得して移動するより、直接クリックする方が確実
        log_message("授業ページを開きました。ブラウザを閉じずに待機します。")

        while True:
            time.sleep(10)

    except Exception:
        log_message("エラーが発生しました。")
        log_message(traceback.format_exc())


if __name__ == "__main__":
    # コマンドライン引数を見て、ワーカーとして実行するか、サーバーとして実行するかを決定
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        # ワーカーとして実行
        open_subject_with_selenium()
    else:
        # サーバーとして実行
        # Flask の reloader で2回開かないように
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
             Timer(0.5, open_browser).start()
        app.run(host="127.0.0.1", port=5000, debug=False)
