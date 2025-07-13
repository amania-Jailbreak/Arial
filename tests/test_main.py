"""
メインアプリケーションのテスト
"""

import pytest
import json
from unittest.mock import patch, Mock


class TestApp:
    """Flaskアプリケーションのテスト"""

    def test_index_page(self, app):
        """インデックスページのテスト"""
        response = app.get("/")
        assert response.status_code == 200
        assert b"Arial" in response.data

    def test_config_api(self, app):
        """設定API のテスト"""
        response = app.get("/api/config")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "download_dir" in data
        assert "aria2_enabled" in data
        assert "plugins_enabled" in data
        assert "available_plugins" in data


class TestDownloadAPI:
    """ダウンロードAPI のテスト"""

    def test_download_api_missing_url(self, app):
        """URL なしでのダウンロードAPI テスト"""
        response = app.post(
            "/api/download", data=json.dumps({}), content_type="application/json"
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data

    @patch("main.plugin_manager")
    def test_download_api_with_plugin(self, mock_manager, app):
        """プラグインを使用したダウンロードAPI テスト"""
        # モックプラグインの設定
        mock_plugin = Mock()
        mock_plugin.can_handle.return_value = True
        mock_plugin.download.return_value = "test_job_id"
        mock_manager.get_plugin_for_url.return_value = mock_plugin

        response = app.post(
            "/api/download",
            data=json.dumps({"url": "https://example.com/file.zip"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "gid" in data

    def test_downloads_list_api(self, app):
        """ダウンロード一覧API のテスト"""
        response = app.get("/api/downloads")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "active" in data
        assert "completed" in data


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""

    def test_make_json_serializable(self):
        """JSON シリアライズ関数のテスト"""
        from main import make_json_serializable
        from datetime import datetime
        from pathlib import Path

        # 基本的なデータ型
        assert make_json_serializable(42) == 42
        assert make_json_serializable("test") == "test"
        assert make_json_serializable(True) is True
        assert make_json_serializable(None) is None

        # 辞書とリスト
        test_dict = {"key": "value", "number": 123}
        assert make_json_serializable(test_dict) == test_dict

        test_list = [1, 2, 3, "test"]
        assert make_json_serializable(test_list) == test_list

        # datetime オブジェクト
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = make_json_serializable(dt)
        assert isinstance(result, str)
        assert "2023-01-01" in result

        # Path オブジェクト
        path = Path("/test/path")
        result = make_json_serializable(path)
        assert isinstance(result, str)
