"""
YouTube-DLプラグイン
YouTube、ニコニコ動画、SNSなどの動画サイト対応
"""

import os
import uuid
import threading
from datetime import datetime
from .base import DownloadPlugin

try:
    import yt_dlp

    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


class YouTubeDLPlugin(DownloadPlugin):
    """YouTube、ニコニコ動画などの動画サイト対応プラグイン"""

    def __init__(self):
        if not YT_DLP_AVAILABLE:
            raise ImportError("yt-dlp is required for YouTubeDLPlugin")

        self.active_downloads = {}
        self.completed_downloads = {}

    def can_handle(self, url: str) -> bool:
        """YouTube、ニコニコ動画、Twitter、Instagramなどの対応サイトをチェック"""
        if not YT_DLP_AVAILABLE:
            return False

        supported_sites = [
            "youtube.com",
            "youtu.be",
            "nicovideo.jp",
            "twitter.com",
            "x.com",
            "instagram.com",
            "tiktok.com",
            "bilibili.com",
            "vimeo.com",
            "twitch.tv",
            "dailymotion.com",
            "soundcloud.com",
        ]
        return any(site in url.lower() for site in supported_sites)

    def get_info(self, url: str) -> dict:
        """動画情報を取得"""
        if not YT_DLP_AVAILABLE:
            return {"error": "yt-dlp not available"}

        try:
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown"),
                    "view_count": info.get("view_count", 0),
                    "formats": len(info.get("formats", [])),
                    "description": (
                        info.get("description", "")[:200] + "..."
                        if info.get("description")
                        else ""
                    ),
                }
        except Exception as e:
            return {"error": str(e)}

    def download(self, url: str, output_path: str = None) -> str:
        """ダウンロードを開始"""
        if not YT_DLP_AVAILABLE:
            raise Exception("yt-dlp not available")

        job_id = str(uuid.uuid4())

        if not output_path:
            output_path = os.path.join(os.getcwd(), "downloads")

        # ダウンロード設定
        ydl_opts = {
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "format": "best[height<=720]/best",  # 720p以下の最高品質、なければ最高品質
            "progress_hooks": [lambda d: self._progress_hook(d, job_id)],
            "writesubtitles": False,  # 字幕をダウンロードしない
            "writeautomaticsub": False,  # 自動生成字幕をダウンロードしない
        }

        self.active_downloads[job_id] = {
            "url": url,
            "status": "downloading",
            "progress": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "speed": 0,
            "eta": 0,
            "filename": "",
            "created_at": datetime.now().isoformat(),
        }

        # 別スレッドでダウンロード実行
        thread = threading.Thread(
            target=self._download_worker, args=(url, ydl_opts, job_id)
        )
        thread.daemon = True
        thread.start()

        return job_id

    def _download_worker(self, url: str, ydl_opts: dict, job_id: str):
        """ダウンロードワーカー"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 完了処理
            if job_id in self.active_downloads:
                download_info = self.active_downloads[job_id]
                self.completed_downloads[job_id] = {
                    **download_info,
                    "status": "completed",
                    "progress": 1.0,
                    "completed_at": datetime.now().isoformat(),
                }
                del self.active_downloads[job_id]

        except Exception as e:
            if job_id in self.active_downloads:
                self.active_downloads[job_id]["status"] = "error"
                self.active_downloads[job_id]["error"] = str(e)

    def _progress_hook(self, d, job_id: str):
        """進捗フック"""
        if job_id not in self.active_downloads:
            return

        download_info = self.active_downloads[job_id]

        if d["status"] == "downloading":
            download_info.update(
                {
                    "downloaded_bytes": d.get("downloaded_bytes", 0),
                    "total_bytes": d.get("total_bytes", 0),
                    "speed": d.get("speed", 0),
                    "eta": d.get("eta", 0),
                    "filename": d.get("filename", ""),
                    "progress": d.get("downloaded_bytes", 0)
                    / max(d.get("total_bytes", 1), 1),
                }
            )
        elif d["status"] == "finished":
            download_info.update(
                {
                    "status": "completed",
                    "progress": 1.0,
                    "filename": d.get("filename", ""),
                }
            )

    def get_progress(self, job_id: str) -> dict:
        """進捗情報を取得"""
        if job_id in self.active_downloads:
            return self.active_downloads[job_id]
        elif job_id in self.completed_downloads:
            return self.completed_downloads[job_id]
        else:
            return {"error": "Job not found"}

    def pause(self, job_id: str) -> bool:
        """一時停止（yt-dlpでは対応していない）"""
        return False

    def resume(self, job_id: str) -> bool:
        """再開（yt-dlpでは対応していない）"""
        return False

    def cancel(self, job_id: str) -> bool:
        """キャンセル"""
        if job_id in self.active_downloads:
            self.active_downloads[job_id]["status"] = "cancelled"
            return True
        return False
