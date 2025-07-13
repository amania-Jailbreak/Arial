#!/bin/bash

# Docker環境での起動スクリプト

# 環境変数の設定
export FLASK_HOST=${FLASK_HOST:-"0.0.0.0"}
export FLASK_PORT=${FLASK_PORT:-5000}
export DOWNLOAD_DIR=${DOWNLOAD_DIR:-"/app/downloads"}

# ダウンロードディレクトリの確認・作成
mkdir -p "$DOWNLOAD_DIR"
chmod 755 "$DOWNLOAD_DIR"

# Arialを起動
echo "Starting Arial Download Manager..."
echo "Host: $FLASK_HOST"
echo "Port: $FLASK_PORT" 
echo "Download Directory: $DOWNLOAD_DIR"

exec python main.py
