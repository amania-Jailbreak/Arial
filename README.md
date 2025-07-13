# Arial - ダウンロードマネージャー

Arial は、aria2 をベースとした高機能なダウンロードマネージャーです。YouTube、ニコニコ動画、Twitter などの動画サイトにも対応したプラグインシステムを搭載しています。

<img src="by-nc-sa.png" alt="alt text" width="80" />

## 特徴

-   🚀 **高速ダウンロード**: aria2 による並列ダウンロード
-   🎥 **動画サイト対応**: YouTube、TikTok、ニコニコ動画など
-   🔧 **プラグインシステム**: 拡張可能なアーキテクチャ
-   🌐 **Web インターフェース**: ブラウザで簡単操作
-   ⚙️ **設定可能**: .env ファイルで簡単設定
-   📊 **リアルタイム進捗**: 定期的な自動更新によるライブ表示

## サポートサイト

### 動画サイト

-   YouTube (youtube.com, youtu.be)
-   ニコニコ動画 (nicovideo.jp)
-   Twitter / X (twitter.com, x.com)
-   Instagram (instagram.com)
-   TikTok (tiktok.com)
-   Bilibili (bilibili.com)
-   Vimeo (vimeo.com)

### ファイルダウンロード

-   HTTP/HTTPS の直接ダウンロード
-   大容量ファイルの分割ダウンロード
-   一時停止・再開機能

## インストール

### 必要環境

-   Python 3.8 以上
-   aria2c (オプション、推奨)

### セットアップ

1. **リポジトリをクローン**

    ```bash
    git clone <repository-url>
    cd Arial
    ```

2. **仮想環境を作成**

    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    # または
    source .venv/bin/activate  # Linux/macOS
    ```

3. **依存関係をインストール**

    ```bash
    pip install -r requirements.txt
    ```

4. **aria2 をインストール (推奨)**
    - Windows: [aria2 releases](https://github.com/aria2/aria2/releases) からダウンロード
    - Ubuntu/Debian: `sudo apt install aria2`
    - macOS: `brew install aria2`

## Docker での使用

### Docker Compose（推奨）

1. **Docker Compose で起動**

    ```bash
    # ダウンロード用ディレクトリを作成
    mkdir downloads

    # バックグラウンドで起動
    docker-compose up -d
    ```

2. **ブラウザでアクセス**

    ```
    http://localhost:5000
    ```

3. **停止**

    ```bash
    docker-compose down
    ```

### 設定のカスタマイズ

`docker-compose.yml` で設定を変更できます：

```yaml
services:
    arial:
        volumes:
            # ダウンロード先を変更
            - /your/download/path:/app/downloads
        environment:
            # 追加の環境変数
            - LOG_LEVEL=DEBUG
```

### Docker 単体での使用

```bash
# イメージをビルド
docker build -t arial .

# コンテナを起動
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/downloads:/app/downloads \
  --name arial-container \
  arial
```

## 使用方法

### 基本的な使い方

1. **アプリケーションを起動**

    ```bash
    python main.py
    ```

2. **ブラウザでアクセス**

    ```
    http://127.0.0.1:5000
    ```

3. **ダウンロードを追加**
    - 「+ Add Download」ボタンをクリック
    - URL を入力して「Add Download」

### 設定

`.env` ファイルで設定をカスタマイズできます：

```properties
# 開発モード
MODE = dev

# ダウンロード先ディレクトリ
DOWNLOAD_DIR = s:\Programs\Arial\downloads
```

## API リファレンス

### ダウンロード管理

#### ダウンロードを追加

```http
POST /api/download
Content-Type: application/json

{
  "url": "https://example.com/file.zip"
}
```

#### ダウンロード一覧を取得

```http
GET /api/downloads
```

#### ダウンロードを一時停止

```http
POST /api/download/{gid}/pause
```

#### ダウンロードを再開

```http
POST /api/download/{gid}/resume
```

#### ダウンロードをキャンセル

```http
POST /api/download/{gid}/cancel
```

### 設定情報

#### 設定を取得

```http
GET /api/config
```

レスポンス例：

```json
{
    "download_dir": "s:\\Programs\\Arial\\downloads",
    "aria2_enabled": true,
    "plugins_enabled": true,
    "available_plugins": ["HTTPDownloadPlugin", "YouTubeDLPlugin"]
}
```

## プラグインシステム

Arial は拡張可能なプラグインアーキテクチャを採用しています。

### 利用可能なプラグイン

1. **HTTPDownloadPlugin**: 標準的な HTTP/HTTPS ダウンロード
2. **YouTubeDLPlugin**: 動画サイト対応（yt-dlp ベース）

### カスタムプラグインの作成

```python
from plugins.base import DownloadPlugin

class MyCustomPlugin(DownloadPlugin):
    def can_handle(self, url: str) -> bool:
        # URL がこのプラグインで処理できるかチェック
        return "mysite.com" in url

    def download(self, url: str, output_path: str = None) -> str:
        # ダウンロード処理を実装
        pass

    # その他の必要なメソッドを実装...
```

## 開発

### プロジェクト構造

```
Arial/
├── main.py              # メインアプリケーション
├── plugins/             # プラグインシステム
│   ├── __init__.py
│   ├── base.py          # 基底クラス
│   ├── http_plugin.py   # HTTP ダウンロード
│   └── youtube_plugin.py # 動画サイト対応
├── templates/           # HTML テンプレート
│   └── index.html
├── src/                 # 静的ファイル
│   └── css/
│       └── style.css
├── requirements.txt     # Python 依存関係
├── .env                 # 環境設定
└── .gitignore
```

### 開発環境のセットアップ

1. **開発依存関係をインストール**

    ```bash
    pip install -r requirements.txt
    ```

2. **デバッグモードで起動**
    ```bash
    python main.py
    ```
    アプリケーションは自動リロード機能付きで起動します。

## トラブルシューティング

### よくある問題

**Q: aria2 が見つからないエラーが出る**
A: aria2c をインストールして PATH に追加してください。または、プラグインシステムのみでも動作します。

**Q: yt-dlp のエラーが出る**
A: 最新版に更新してください：`pip install --upgrade yt-dlp`

**Q: ダウンロードが開始されない**
A: URL が正しいか、サイトがサポートされているか確認してください。

**Q: プラグインが読み込まれない**
A: 依存関係がインストールされているか確認してください。

### ログの確認

アプリケーションは詳細なログを出力します：

-   コンソールでリアルタイムログを確認
-   ログレベル: INFO, WARNING, ERROR

## 貢献

バグ報告や機能要望は Issue でお知らせください。プルリクエストも歓迎します！

### 開発に参加する場合

1. Fork してください
2. フィーチャーブランチを作成: `git checkout -b feature/amazing-feature`
3. 変更をコミット: `git commit -m 'Add amazing feature'`
4. ブランチにプッシュ: `git push origin feature/amazing-feature`
5. Pull Request を作成

## 関連プロジェクト

-   [aria2](https://github.com/aria2/aria2) - 高速ダウンローダー
-   [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube ダウンローダー
-   [Flask](https://flask.palletsprojects.com/) - Python ウェブフレームワーク

## Git ワークフロー

### ブランチ戦略

```bash
# 新機能開発
git checkout -b feature/add-torrent-support

# バグ修正
git checkout -b fix/youtube-download-error

# ドキュメント更新
git checkout -b docs/update-api-reference
```

### コミットメッセージ規約

```
<type>(<scope>): <subject>

例:
feat(plugin): BitTorrentダウンロード対応プラグインを追加
fix(ui): プログレスバーの表示エラーを修正
docs: Docker使用方法をREADMEに追加
```

#### Type

-   `feat`: 新機能
-   `fix`: バグ修正
-   `docs`: ドキュメント
-   `style`: コードスタイル
-   `refactor`: リファクタリング
-   `test`: テスト関連
-   `chore`: その他

#### Scope (オプション)

-   `core`: コアシステム
-   `plugin`: プラグインシステム
-   `ui`: ユーザーインターフェース
-   `api`: REST API
-   `docker`: Docker 関連

### 開発ワークフロー

1. **Issue 作成**: 機能要求やバグ報告
2. **ブランチ作成**: Issue 番号を含む名前
3. **開発**: 小さなコミットで段階的に
4. **テスト**: 変更内容の動作確認
5. **Pull Request**: レビューを依頼
6. **マージ**: レビュー完了後に main ブランチへ

---

作成者: amania

最終更新: 2025 年 7 月 13 日

製作補助: Claude Sonnet 4, GPT4.1, GPT4.1-mini,GPT4o-mini
