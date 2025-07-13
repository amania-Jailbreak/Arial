from flask import Flask, request, jsonify, render_template, send_file
import flask_cors
import json
import subprocess
import aria2p
import logging
from dotenv import load_dotenv
import os
import threading
import time
from datetime import datetime
import uuid
from pathlib import Path
import sys

# プラグインシステムのインポート
from plugins import PluginManager

# 環境変数読み込み
load_dotenv()

# デフォルトダウンロードディレクトリの設定
DEFAULT_DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", os.path.join(os.getcwd(), "downloads"))
os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)


# ユーティリティ関数
def make_json_serializable(obj):
    """オブジェクトをJSON serializable に変換"""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, "total_seconds"):  # timedelta
        return int(obj.total_seconds())
    elif hasattr(obj, "isoformat"):  # datetime
        return obj.isoformat()
    elif isinstance(obj, (Path, os.PathLike)):  # Path objects
        return str(obj)
    elif obj is None:
        return None
    elif isinstance(obj, (int, float, str, bool)):
        return obj
    else:
        # その他のオブジェクトは文字列に変換
        return str(obj)


app = Flask(__name__, static_folder="src")
flask_cors.CORS(app)

# グローバル変数
download_jobs = {}
completed_jobs = {}
plugin_jobs = {}  # プラグイン用のジョブ管理
aria2_process = None
aria2_api = None
plugin_manager = None


def initialize_plugins():
    """プラグインシステムを初期化"""
    global plugin_manager
    try:
        plugin_manager = PluginManager()
        logging.info("Plugin system initialized successfully")
        return True
    except ImportError as e:
        logging.warning(f"Some plugins unavailable due to missing dependencies: {e}")
        # yt_dlpがインストールされていない場合は、HTTPプラグインのみ使用
        try:

            class BasicPluginManager:
                def __init__(self):
                    from plugins.http_plugin import HTTPDownloadPlugin

                    self.plugins = [HTTPDownloadPlugin()]

                def get_plugin_for_url(self, url: str):
                    for plugin in self.plugins:
                        if plugin.can_handle(url):
                            return plugin
                    return None

                def get_all_plugins(self):
                    return self.plugins

            plugin_manager = BasicPluginManager()
            logging.info("Plugin system initialized with HTTP plugin only")
            return True
        except Exception as e2:
            logging.error(f"Failed to initialize even basic plugins: {e2}")
            return False
    except Exception as e:
        logging.error(f"Failed to initialize plugins: {e}")
        return False


# Aria2サーバーの起動
def start_aria2():
    global aria2_process, aria2_api
    try:
        # Aria2サーバーを起動
        aria2_process = subprocess.Popen(
            [
                "aria2c",
                "--enable-rpc",
                "--rpc-listen-all",
                "--rpc-allow-origin-all",
                "--rpc-listen-port=6800",
                "--continue=true",
                "--max-connection-per-server=16",
                "--min-split-size=1M",
                "--split=16",
                f"--dir={DEFAULT_DOWNLOAD_DIR}",
            ]
        )

        # 少し待ってからAPIクライアントを初期化
        time.sleep(2)
        aria2_api = aria2p.API(
            aria2p.Client(host="http://localhost", port=6800, secret="")
        )
        logging.info("Aria2 server started successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to start Aria2: {e}")
        return False


# ダウンロード情報を更新する関数
def update_download_info():
    global download_jobs, completed_jobs, aria2_api

    while True:
        try:
            if aria2_api:
                # アクティブなダウンロードを取得
                active_downloads = aria2_api.get_downloads()

                # 現在のジョブを更新
                current_gids = []
                for download in active_downloads:
                    gid = download.gid
                    current_gids.append(gid)

                    # ETA を秒数に変換（timedelta から int へ）
                    eta_seconds = None
                    if download.eta and hasattr(download.eta, "total_seconds"):
                        eta_seconds = int(download.eta.total_seconds())
                    elif download.eta and isinstance(download.eta, (int, float)):
                        eta_seconds = int(download.eta)

                    if gid in download_jobs:
                        # 既存のジョブを更新
                        job = download_jobs[gid]

                        # 完了をチェック（進捗率100%または状態がcomplete）
                        if (
                            download.status in ["complete", "removed"]
                            or (download.progress and float(download.progress) >= 1.0)
                            or (
                                download.total_length
                                and download.completed_length
                                and download.completed_length >= download.total_length
                            )
                        ):

                            # 完了したジョブを移動
                            completed_jobs[gid] = {
                                "gid": gid,
                                "name": job["name"],
                                "total_length": (
                                    int(download.total_length)
                                    if download.total_length
                                    else job.get("total_length", 0)
                                ),
                                "completed_at": datetime.now().isoformat(),
                                "file_path": (
                                    str(download.files[0].path)
                                    if download.files
                                    else ""
                                ),
                            }
                            # アクティブなダウンロードから削除
                            del download_jobs[gid]
                            continue  # 完了済みなので更新処理をスキップ

                        # アクティブなジョブの更新
                        job.update(
                            {
                                "progress": (
                                    float(download.progress)
                                    if download.progress
                                    else 0.0
                                ),
                                "download_speed": (
                                    int(download.download_speed)
                                    if download.download_speed
                                    else 0
                                ),
                                "eta": eta_seconds,
                                "completed_length": (
                                    int(download.completed_length)
                                    if download.completed_length
                                    else 0
                                ),
                                "total_length": (
                                    int(download.total_length)
                                    if download.total_length
                                    else 0
                                ),
                                "status": str(download.status),
                                "updated_at": datetime.now().isoformat(),
                            }
                        )
                    else:
                        # 新しいジョブを追加
                        # 進捗率を計算（0-1の範囲に制限）
                        progress = 0.0
                        if download.total_length and download.completed_length:
                            progress = min(
                                float(download.completed_length)
                                / float(download.total_length),
                                1.0,
                            )
                        elif download.progress:
                            # aria2pのprogressが既にパーセンテージ（0-100）の場合
                            progress = min(float(download.progress) / 100.0, 1.0)

                        # 新しいジョブがすでに完了している場合は完了リストに追加
                        if (
                            download.status in ["complete", "removed"]
                            or progress >= 1.0
                            or (
                                download.total_length
                                and download.completed_length
                                and download.completed_length >= download.total_length
                            )
                        ):

                            completed_jobs[gid] = {
                                "gid": gid,
                                "name": (
                                    str(download.name) if download.name else "Unknown"
                                ),
                                "total_length": (
                                    int(download.total_length)
                                    if download.total_length
                                    else 0
                                ),
                                "completed_at": datetime.now().isoformat(),
                                "file_path": (
                                    str(download.files[0].path)
                                    if download.files
                                    else ""
                                ),
                            }
                        else:
                            # アクティブなジョブとして追加
                            download_jobs[gid] = {
                                "gid": gid,
                                "name": (
                                    str(download.name) if download.name else "Unknown"
                                ),
                                "progress": progress,
                                "download_speed": (
                                    int(download.download_speed)
                                    if download.download_speed
                                    else 0
                                ),
                                "eta": eta_seconds,
                                "completed_length": (
                                    int(download.completed_length)
                                    if download.completed_length
                                    else 0
                                ),
                                "total_length": (
                                    int(download.total_length)
                                    if download.total_length
                                    else 0
                                ),
                                "status": str(download.status),
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat(),
                            }

                # 削除されたジョブをクリーンアップ
                jobs_to_remove = [
                    gid for gid in download_jobs.keys() if gid not in current_gids
                ]
                for gid in jobs_to_remove:
                    if gid in download_jobs:
                        del download_jobs[gid]

        except Exception as e:
            logging.error(f"Error updating download info: {e}")

        # プラグインからの進捗も更新
        try:
            if plugin_manager:
                for plugin in plugin_manager.get_all_plugins():
                    # アクティブなダウンロードをチェック
                    if hasattr(plugin, "active_downloads"):
                        for job_id, job_info in plugin.active_downloads.items():
                            plugin_key = f"plugin_{job_id}"
                            download_jobs[plugin_key] = {
                                "gid": plugin_key,
                                "name": job_info.get("filename", "Unknown"),
                                "progress": job_info.get("progress", 0.0),
                                "download_speed": job_info.get("speed", 0),
                                "eta": job_info.get("eta", 0),
                                "completed_length": job_info.get("downloaded_bytes", 0),
                                "total_length": job_info.get("total_bytes", 0),
                                "status": job_info.get("status", "active"),
                                "plugin_type": plugin.__class__.__name__,
                                "created_at": job_info.get(
                                    "created_at", datetime.now().isoformat()
                                ),
                                "updated_at": datetime.now().isoformat(),
                            }

                    # 完了したダウンロードをチェック
                    if hasattr(plugin, "completed_downloads"):
                        for job_id, job_info in plugin.completed_downloads.items():
                            plugin_key = f"plugin_{job_id}"
                            if plugin_key not in completed_jobs:
                                completed_jobs[plugin_key] = {
                                    "gid": plugin_key,
                                    "name": job_info.get("filename", "Unknown"),
                                    "total_length": job_info.get("total_bytes", 0),
                                    "completed_at": job_info.get(
                                        "completed_at", datetime.now().isoformat()
                                    ),
                                    "file_path": job_info.get("file_path", ""),
                                    "plugin_type": plugin.__class__.__name__,
                                }
                                # アクティブリストから削除
                                if plugin_key in download_jobs:
                                    del download_jobs[plugin_key]
        except Exception as e:
            logging.error(f"Error updating plugin download info: {e}")

        time.sleep(1)  # 1秒ごとに更新


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    """設定情報を取得"""
    return jsonify(
        {
            "download_dir": DEFAULT_DOWNLOAD_DIR,
            "aria2_enabled": aria2_api is not None,
            "plugins_enabled": plugin_manager is not None,
            "available_plugins": [
                plugin.__class__.__name__
                for plugin in (
                    plugin_manager.get_all_plugins() if plugin_manager else []
                )
            ],
        }
    )


# API エンドポイント
@app.route("/api/downloads", methods=["GET"])
def get_downloads():
    """現在のダウンロード一覧を取得"""
    try:
        # データをJSON serializable に変換
        active_data = make_json_serializable(list(download_jobs.values()))
        completed_data = make_json_serializable(list(completed_jobs.values()))

        return jsonify(
            {
                "active": active_data,
                "completed": completed_data,
            }
        )
    except Exception as e:
        logging.error(f"Error getting downloads: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def add_download():
    """新しいダウンロードを追加"""
    try:
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "URL is required"}), 400

        # プラグインシステムを最初にチェック
        if plugin_manager:
            plugin = plugin_manager.get_plugin_for_url(url)
            if plugin:
                try:
                    job_id = plugin.download(url, DEFAULT_DOWNLOAD_DIR)
                    return jsonify(
                        {
                            "success": True,
                            "gid": f"plugin_{job_id}",
                            "plugin": plugin.__class__.__name__,
                        }
                    )
                except Exception as e:
                    logging.error(f"Plugin download failed: {e}")
                    # プラグインが失敗した場合はaria2にフォールバック

        # aria2を使用
        if not aria2_api:
            return jsonify({"error": "No download method available"}), 500

        # ダウンロードを開始（ダウンロードディレクトリを指定）
        download = aria2_api.add_uris([url], options={"dir": DEFAULT_DOWNLOAD_DIR})

        return jsonify({"success": True, "gid": download.gid})
    except Exception as e:
        logging.error(f"Error adding download: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<gid>/pause", methods=["POST"])
def pause_download(gid):
    """ダウンロードを一時停止"""
    try:
        # プラグインジョブかチェック
        if gid.startswith("plugin_"):
            job_id = gid[7:]  # "plugin_" を除去
            if plugin_manager:
                for plugin in plugin_manager.get_all_plugins():
                    if (
                        hasattr(plugin, "active_downloads")
                        and job_id in plugin.active_downloads
                    ):
                        success = plugin.pause(job_id)
                        if success:
                            return jsonify(
                                {"success": True, "message": "Download paused"}
                            )
                        else:
                            return (
                                jsonify(
                                    {"error": "Pause not supported by this plugin"}
                                ),
                                400,
                            )
            return jsonify({"error": "Plugin job not found"}), 404

        # aria2ジョブ
        if not aria2_api:
            return jsonify({"error": "Aria2 not available"}), 500

        aria2_api.pause([gid])
        return jsonify({"success": True, "message": "Download paused"})

    except Exception as e:
        logging.error(f"Error pausing download: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<gid>/resume", methods=["POST"])
def resume_download(gid):
    """ダウンロードを再開"""
    try:
        # プラグインジョブかチェック
        if gid.startswith("plugin_"):
            job_id = gid[7:]
            if plugin_manager:
                for plugin in plugin_manager.get_all_plugins():
                    if (
                        hasattr(plugin, "active_downloads")
                        and job_id in plugin.active_downloads
                    ):
                        success = plugin.resume(job_id)
                        if success:
                            return jsonify(
                                {"success": True, "message": "Download resumed"}
                            )
                        else:
                            return (
                                jsonify(
                                    {"error": "Resume not supported by this plugin"}
                                ),
                                400,
                            )
            return jsonify({"error": "Plugin job not found"}), 404

        # aria2ジョブ
        if not aria2_api:
            return jsonify({"error": "Aria2 not available"}), 500

        aria2_api.resume([gid])
        return jsonify({"success": True, "message": "Download resumed"})

    except Exception as e:
        logging.error(f"Error resuming download: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<gid>/cancel", methods=["POST"])
def cancel_download(gid):
    """ダウンロードをキャンセル"""
    try:
        # プラグインジョブかチェック
        if gid.startswith("plugin_"):
            job_id = gid[7:]
            if plugin_manager:
                for plugin in plugin_manager.get_all_plugins():
                    if (
                        hasattr(plugin, "active_downloads")
                        and job_id in plugin.active_downloads
                    ):
                        success = plugin.cancel(job_id)
                        if success:
                            return jsonify(
                                {"success": True, "message": "Download cancelled"}
                            )
                        else:
                            return jsonify({"error": "Cancel failed"}), 400
            return jsonify({"error": "Plugin job not found"}), 404

        # aria2ジョブ
        if not aria2_api:
            return jsonify({"error": "Aria2 not available"}), 500

        aria2_api.remove([gid])

        # ローカルからも削除
        if gid in download_jobs:
            del download_jobs[gid]

        return jsonify({"success": True, "message": "Download cancelled"})

    except Exception as e:
        logging.error(f"Error cancelling download: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/plugins", methods=["GET"])
def get_plugins():
    """利用可能なプラグイン一覧を取得"""
    try:
        if not plugin_manager:
            return jsonify({"plugins": [], "message": "Plugin system not available"})

        plugins_info = []
        for plugin in plugin_manager.get_all_plugins():
            plugins_info.append(
                {
                    "name": plugin.__class__.__name__,
                    "type": plugin.__class__.__name__.replace("Plugin", ""),
                    "description": plugin.__doc__ or "No description available",
                }
            )

        return jsonify({"plugins": plugins_info, "total": len(plugins_info)})

    except Exception as e:
        logging.error(f"Error getting plugins: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/completed/<gid>/delete", methods=["POST"])
def delete_completed(gid):
    """完了したダウンロードを削除"""
    try:
        if gid in completed_jobs:
            # ファイルも削除するかどうかの確認
            data = request.get_json() or {}
            delete_file = data.get("delete_file", False)

            if delete_file and "file_path" in completed_jobs[gid]:
                file_path = completed_jobs[gid]["file_path"]
                if os.path.exists(file_path):
                    os.remove(file_path)

            del completed_jobs[gid]
            return jsonify({"success": True, "message": "Completed job deleted"})
        else:
            return jsonify({"error": "Job not found"}), 404

    except Exception as e:
        logging.error(f"Error deleting completed job: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """統計情報を取得"""
    try:
        total_active = len(download_jobs)
        total_completed = len(completed_jobs)
        total_speed = sum(
            job.get("download_speed", 0) for job in download_jobs.values()
        )

        stats_data = {
            "active_downloads": total_active,
            "completed_downloads": total_completed,
            "total_download_speed": int(total_speed),
        }

        return jsonify(make_json_serializable(stats_data))

    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/file/<gid>", methods=["GET"])
def download_file(gid):
    """完了したファイルをダウンロード"""
    try:
        if gid in completed_jobs:
            completed_job = completed_jobs[gid]
            file_path = completed_job.get("file_path")

            if file_path and os.path.exists(file_path):
                filename = completed_job.get("name", "download")
                return send_file(file_path, as_attachment=True, download_name=filename)
            else:
                return jsonify({"error": "File not found"}), 404
        else:
            return jsonify({"error": "Job not found"}), 404

    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 500


# ユーティリティ関数
def make_json_serializable(obj):
    """オブジェクトをJSON serializable に変換"""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, "total_seconds"):  # timedelta
        return int(obj.total_seconds())
    elif hasattr(obj, "isoformat"):  # datetime
        return obj.isoformat()
    elif obj is None:
        return None
    else:
        return obj


def format_bytes(bytes_value):
    """バイト数を読みやすい形式に変換"""
    if bytes_value == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_value >= 1024 and i < len(size_names) - 1:
        bytes_value /= 1024
        i += 1

    return f"{bytes_value:.1f}{size_names[i]}"


def format_time(seconds):
    """秒数を読みやすい時間形式に変換"""
    if seconds is None or seconds < 0:
        return "Unknown"

    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        return f"{int(seconds // 60)}分"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}時間{minutes}分"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Arial")
    print = logger.info
    print("Starting Arial...")
    load_dotenv()

    # プラグインシステムを初期化
    initialize_plugins()

    # Aria2サーバーを起動
    if start_aria2():
        print("Aria2 server started successfully")

        # バックグラウンドでダウンロード情報を更新
        update_thread = threading.Thread(target=update_download_info, daemon=True)
        update_thread.start()
        print("Download monitor started")

        # Flaskサーバーを起動
        if os.getenv("MODE") == "dev":
            print("Running in development mode")
            app.run(debug=True, host="0.0.0.0", port=5000)
        else:
            print("Running in production mode")
            app.run(host="0.0.0.0", port=80)
    else:
        print("Failed to start Aria2 server. Plugin system only mode...")
        if plugin_manager:
            print("Running with plugin system only")
            # バックグラウンドでダウンロード情報を更新
            update_thread = threading.Thread(target=update_download_info, daemon=True)
            update_thread.start()
            print("Download monitor started")

            if os.getenv("MODE") == "dev":
                print("Running in development mode")
                app.run(debug=True, host="0.0.0.0", port=5000)
            else:
                print("Running in production mode")
                app.run(host="0.0.0.0", port=80)
        else:
            print("Failed to start any download system. Exiting...")
            exit(1)
