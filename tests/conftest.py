"""
pytest 設定とフィクスチャ
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch


@pytest.fixture
def app():
    """Flaskアプリケーションのテスト用フィクスチャ"""
    # テスト用の環境変数設定
    os.environ["FLASK_ENV"] = "testing"
    os.environ["DOWNLOAD_DIR"] = tempfile.mkdtemp()

    # アプリケーションをインポート
    from main import app

    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def temp_download_dir():
    """一時ダウンロードディレクトリ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # クリーンアップは自動的に行われる


@pytest.fixture
def mock_aria2():
    """aria2 API のモック"""
    with patch("main.aria2_api") as mock_api:
        mock_api.add_uris.return_value = Mock(gid="test_gid_123")
        mock_api.get_downloads.return_value = []
        yield mock_api


@pytest.fixture
def mock_plugin_manager():
    """プラグインマネージャーのモック"""
    with patch("main.plugin_manager") as mock_manager:
        mock_plugin = Mock()
        mock_plugin.can_handle.return_value = True
        mock_plugin.download.return_value = "plugin_job_123"
        mock_plugin.get_progress.return_value = {
            "status": "downloading",
            "progress": 0.5,
            "speed": 1024000,
        }
        mock_manager.get_plugin_for_url.return_value = mock_plugin
        mock_manager.get_all_plugins.return_value = [mock_plugin]
        yield mock_manager


@pytest.fixture
def sample_urls():
    """テスト用のサンプルURL"""
    return {
        "http_file": "https://httpbin.org/uuid",
        "youtube": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "invalid": "not_a_url",
    }
