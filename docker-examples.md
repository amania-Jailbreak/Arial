# Arial Docker 使用例

## 基本的な使用方法

### 1. シンプルな起動

```bash
# プロジェクトディレクトリに移動
cd Arial

# Docker Composeで起動
docker-compose up -d

# ログを確認
docker-compose logs -f arial
```

### 2. カスタムダウンロードディレクトリ

```bash
# ホストの任意のディレクトリを指定
docker run -d \
  -p 5000:5000 \
  -v /home/user/Downloads:/app/downloads \
  --name arial \
  arial
```

### 3. 環境変数での設定

```bash
# ログレベルを変更
docker-compose up -d -e LOG_LEVEL=DEBUG

# カスタムポートで起動
docker run -d \
  -p 8080:5000 \
  -v $(pwd)/downloads:/app/downloads \
  -e FLASK_PORT=5000 \
  arial
```

## 開発用設定

### ソースコードをマウントして開発

```bash
docker run -d \
  -p 5000:5000 \
  -v $(pwd):/app \
  -v $(pwd)/downloads:/app/downloads \
  --name arial-dev \
  arial
```

## トラブルシューティング

### ログの確認

```bash
# Arialのログ
docker-compose logs arial

# aria2のログ
docker-compose logs aria2

# 全サービスのログ
docker-compose logs
```

### コンテナに接続

```bash
# Arialコンテナに接続
docker exec -it arial-download-manager bash

# aria2コンテナに接続
docker exec -it arial-aria2 bash
```

### 設定の確認

```bash
# 設定APIを呼び出し
curl http://localhost:5000/api/config

# コンテナ内の環境変数確認
docker exec arial-download-manager printenv
```

## ポート設定

-   **5000**: Arial WebUI
-   **6800**: aria2 RPC（内部通信用）
-   **6888**: aria2 listen port

## ボリューム設定

-   `./downloads:/app/downloads` - ダウンロードファイル
-   `./.env:/app/.env:ro` - 設定ファイル（読み取り専用）
-   `./aria2-config:/config` - aria2 設定ファイル

## ネットワーク

Docker Compose では`arial-network`という専用ネットワークを使用し、
Arial と Aria2 が内部で通信できるようになっています。
