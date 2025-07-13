# Python 3.11をベースイメージとして使用
FROM python:3.11-slim

# メンテナー情報
LABEL maintainer="amania"
LABEL description="Arial - Advanced Download Manager with aria2 and plugin system"

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ffmpeg \
    aria2 \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# Pythonの依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係をインストール
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# ダウンロードディレクトリを作成
RUN mkdir -p /app/downloads

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# 非rootユーザーに切り替え
USER app

# ポート5000を公開
EXPOSE 5000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/config || exit 1

# アプリケーションを起動
CMD ["python", "main.py"]
