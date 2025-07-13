"""
HTTPダウンロードプラグイン
標準的なHTTP/HTTPSファイルダウンロードに対応
"""

import os
import time
import uuid
import requests
import threading
from datetime import datetime
from .base import DownloadPlugin


class HTTPDownloadPlugin(DownloadPlugin):
    """標準的なHTTPダウンロード対応プラグイン"""

    def __init__(self):
        self.active_downloads = {}
        self.completed_downloads = {}

    def can_handle(self, url: str) -> bool:
        """HTTP/HTTPSのファイル直リンクをチェック"""
        return url.startswith(("http://", "https://")) and not self._is_webpage(url)

    def _is_webpage(self, url: str) -> bool:
        """Webページかどうかを簡易判定"""
        try:
            response = requests.head(url, timeout=5)
            content_type = response.headers.get("content-type", "").lower()
            return "text/html" in content_type
        except:
            return False

    def get_info(self, url: str) -> dict:
        """ファイル情報を取得"""
        try:
            response = requests.head(url, timeout=10)
            filename = self._get_filename_from_url(url, response)
            file_size = int(response.headers.get("content-length", 0))

            return {
                "filename": filename,
                "size": file_size,
                "content_type": response.headers.get("content-type", "Unknown"),
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_filename_from_url(self, url: str, response) -> str:
        """URLからファイル名を取得"""
        # Content-Dispositionヘッダーから取得
        cd = response.headers.get("content-disposition")
        if cd:
            import re

            filename = re.findall("filename=(.+)", cd)
            if filename:
                return filename[0].strip('"')

        # URLから取得
        return os.path.basename(url.split("?")[0]) or "downloaded_file"

    def download(self, url: str, output_path: str = None) -> str:
        """ダウンロードを開始"""
        job_id = str(uuid.uuid4())

        if not output_path:
            output_path = os.path.join(os.getcwd(), "downloads")

        # ダウンロード情報を初期化
        self.active_downloads[job_id] = {
            "url": url,
            "status": "downloading",
            "progress": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "speed": 0,
            "filename": "",
            "output_path": output_path,
            "created_at": datetime.now().isoformat(),
        }

        # 別スレッドでダウンロード実行
        thread = threading.Thread(
            target=self._download_worker, args=(url, output_path, job_id)
        )
        thread.daemon = True
        thread.start()

        return job_id

    def _download_worker(self, url: str, output_path: str, job_id: str):
        """ダウンロードワーカー"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            filename = self._get_filename_from_url(url, response)
            full_path = os.path.join(output_path, filename)

            # ディレクトリ作成
            os.makedirs(output_path, exist_ok=True)

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            self.active_downloads[job_id].update(
                {"filename": filename, "total_bytes": total_size}
            )

            with open(full_path, "wb") as f:
                start_time = time.time()
                for chunk in response.iter_content(chunk_size=8192):
                    if self.active_downloads[job_id]["status"] == "cancelled":
                        break

                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 進捗更新
                        elapsed_time = time.time() - start_time
                        speed = downloaded_size / max(elapsed_time, 1)
                        progress = (
                            downloaded_size / max(total_size, 1)
                            if total_size > 0
                            else 0
                        )

                        self.active_downloads[job_id].update(
                            {
                                "downloaded_bytes": downloaded_size,
                                "progress": progress,
                                "speed": speed,
                            }
                        )

            # 完了処理
            if self.active_downloads[job_id]["status"] != "cancelled":
                download_info = self.active_downloads[job_id]
                self.completed_downloads[job_id] = {
                    **download_info,
                    "status": "completed",
                    "progress": 1.0,
                    "file_path": full_path,
                    "completed_at": datetime.now().isoformat(),
                }
                del self.active_downloads[job_id]

        except Exception as e:
            if job_id in self.active_downloads:
                self.active_downloads[job_id]["status"] = "error"
                self.active_downloads[job_id]["error"] = str(e)

    def get_progress(self, job_id: str) -> dict:
        """進捗情報を取得"""
        if job_id in self.active_downloads:
            return self.active_downloads[job_id]
        elif job_id in self.completed_downloads:
            return self.completed_downloads[job_id]
        else:
            return {"error": "Job not found"}

    def pause(self, job_id: str) -> bool:
        """一時停止（簡易実装では対応しない）"""
        return False

    def resume(self, job_id: str) -> bool:
        """再開（簡易実装では対応しない）"""
        return False

    def cancel(self, job_id: str) -> bool:
        """キャンセル"""
        if job_id in self.active_downloads:
            self.active_downloads[job_id]["status"] = "cancelled"
            return True
        return False
