"""
プラグインの基底クラスとインターフェース
"""

from abc import ABC, abstractmethod
import logging


class DownloadPlugin(ABC):
    """ダウンロードプラグインの基底クラス"""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """このプラグインがURLを処理できるかチェック"""
        pass

    @abstractmethod
    def get_info(self, url: str) -> dict:
        """ダウンロード情報を取得"""
        pass

    @abstractmethod
    def download(self, url: str, output_path: str = None) -> str:
        """ダウンロードを実行し、ジョブIDを返す"""
        pass

    @abstractmethod
    def get_progress(self, job_id: str) -> dict:
        """ダウンロード進捗を取得"""
        pass

    @abstractmethod
    def pause(self, job_id: str) -> bool:
        """ダウンロードを一時停止"""
        pass

    @abstractmethod
    def resume(self, job_id: str) -> bool:
        """ダウンロードを再開"""
        pass

    @abstractmethod
    def cancel(self, job_id: str) -> bool:
        """ダウンロードをキャンセル"""
        pass


class PluginManager:
    """プラグインマネージャー"""

    def __init__(self):
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        """利用可能なプラグインを読み込み"""
        self.plugins = []

        # HTTPダウンロードプラグインは常に追加
        try:
            from .http_plugin import HTTPDownloadPlugin

            self.plugins.append(HTTPDownloadPlugin())
            logging.info("HTTPDownloadPlugin loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load HTTPDownloadPlugin: {e}")

        # YouTube-DLプラグインは条件付きで追加
        try:
            import yt_dlp  # インポートテスト
            from .youtube_plugin import YouTubeDLPlugin

            self.plugins.append(YouTubeDLPlugin())
            logging.info("YouTubeDLPlugin loaded successfully")
        except ImportError:
            logging.warning("yt-dlp not available, YouTubeDLPlugin disabled")
        except Exception as e:
            logging.error(f"Failed to load YouTubeDLPlugin: {e}")

    def get_plugin_for_url(self, url: str) -> DownloadPlugin:
        """URLに適したプラグインを取得"""
        for plugin in self.plugins:
            if plugin.can_handle(url):
                return plugin
        return None

    def get_all_plugins(self) -> list:
        """全プラグインを取得"""
        return self.plugins

    def reload_plugins(self):
        """プラグインを再読み込み"""
        self.load_plugins()
