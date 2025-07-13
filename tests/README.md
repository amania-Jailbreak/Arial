# テストファイル一覧

このディレクトリには以下のテストファイルが含まれます：

-   `test_main.py` - メインアプリケーションのテスト
-   `test_plugins/` - プラグインシステムのテスト
-   `test_api.py` - REST API のテスト
-   `conftest.py` - pytest 設定とフィクスチャ

## テスト実行方法

```bash
# 全テスト実行
pytest

# カバレッジ付きテスト実行
pytest --cov=. --cov-report=html

# 特定のテストファイル実行
pytest tests/test_main.py

# 特定のテスト関数実行
pytest tests/test_main.py::test_app_initialization
```

## テスト環境セットアップ

```bash
pip install pytest pytest-cov pytest-mock
```
