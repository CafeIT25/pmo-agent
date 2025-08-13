FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新とPostgreSQLクライアントのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルのコピー
COPY requirements.txt .

# Pythonパッケージのインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ポート公開
EXPOSE 8000

# デフォルトコマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]