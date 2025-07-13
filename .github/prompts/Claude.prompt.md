---
mode: agent
---

# Arial プロジェクト - Claude AI アシスタント システムプロンプト

## プロジェクト概要

Arial は aria2 をベースとした高機能なダウンロードマネージャーです。プラグインシステムにより YouTube、ニコニコ動画、Twitter などの動画サイトにも対応しています。

### 技術スタック

-   **Backend**: Python (Flask)
-   **Frontend**: HTML/CSS/JavaScript
-   **Download Engine**: aria2 + yt-dlp
-   **Architecture**: Plugin System
-   **Deployment**: Docker / Docker Compose

## Git ワークフロー ガイドライン

### ブランチ戦略

1. **main ブランチ**: 本番環境対応の安定版
2. **develop ブランチ**: 開発統合ブランチ
3. **feature/xxx ブランチ**: 新機能開発
4. **fix/xxx ブランチ**: バグ修正
5. **docs/xxx ブランチ**: ドキュメント更新

### コミットメッセージ規約

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type (必須)

-   `feat`: 新機能
-   `fix`: バグ修正
-   `docs`: ドキュメント
-   `style`: コードスタイル修正
-   `refactor`: リファクタリング
-   `perf`: パフォーマンス改善
-   `test`: テスト追加・修正
-   `chore`: ビルド・設定変更
-   `ci`: CI/CD 関連

#### Scope (オプション)

-   `core`: コアシステム
-   `plugin`: プラグインシステム
-   `ui`: ユーザーインターフェース
-   `api`: REST API
-   `docker`: Docker 関連
-   `config`: 設定関連

#### 例

```
feat(plugin): YouTubeプラグインに字幕ダウンロード機能を追加

- yt-dlp の writesubtitles オプションを有効化
- 字幕言語選択機能を実装
- UIに字幕ダウンロードチェックボックスを追加

Closes #123
```

### AI アシスタント向け Git 操作指針

#### 1. 変更前の状況確認

```bash
# 現在のブランチとステータス確認
git status
git branch

# 最新の変更履歴確認
git log --oneline -10

# 未コミットの変更確認
git diff
```

#### 2. 適切なブランチでの作業

```bash
# 新機能開発の場合
git checkout -b feature/add-torrent-support

# バグ修正の場合
git checkout -b fix/youtube-download-error

# ドキュメント更新の場合
git checkout -b docs/update-readme
```

#### 3. コミット前のチェック

```bash
# 変更内容を段階的に確認
git add -p

# コミット前の最終確認
git diff --cached

# 適切なコミットメッセージでコミット
git commit -m "feat(plugin): Torrentダウンロード対応プラグインを追加"
```

#### 4. プッシュとプルリクエスト

```bash
# リモートにプッシュ
git push origin feature/add-torrent-support

# main ブランチとの差分確認
git diff main..HEAD
```

### コード品質維持

#### コードレビューポイント

1. **セキュリティ**: 入力検証、XSS 対策
2. **パフォーマンス**: メモリリーク、CPU 使用率
3. **可読性**: コメント、変数名の明確性
4. **テスト**: 単体テスト、統合テスト
5. **互換性**: Python バージョン、依存関係

#### 自動化チェック

-   **Linting**: flake8, black
-   **Security**: bandit
-   **Dependencies**: safety check
-   **Documentation**: docstring coverage

### ファイル管理ルール

#### 重要ファイルの変更時注意事項

-   `main.py`: アプリケーションコア → 慎重にテスト
-   `plugins/`: プラグインシステム → 後方互換性確保
-   `requirements.txt`: 依存関係 → バージョン固定
-   `docker-compose.yml`: インフラ → 本番環境影響考慮
-   `.env`: 設定ファイル → セキュリティ情報漏洩注意

#### 無視すべきファイル (.gitignore)

-   `downloads/`: ダウンロードファイル
-   `__pycache__/`: Python キャッシュ
-   `.env`: 環境設定（機密情報）
-   `*.log`: ログファイル
-   `.vscode/`, `.idea/`: IDE 設定

### 緊急対応プロセス

#### 本番環境での問題発生時

1. **hotfix ブランチ作成**: `git checkout -b hotfix/critical-bug-fix`
2. **最小限の修正**: 問題の根本原因のみ修正
3. **即座にテスト**: 影響範囲を確認
4. **main ブランチに直接マージ**: レビュー後即座に適用
5. **develop ブランチにも反映**: `git cherry-pick`

### リリース管理

#### バージョニング (Semantic Versioning)

-   **MAJOR**: 非互換な API 変更
-   **MINOR**: 後方互換性のある機能追加
-   **PATCH**: 後方互換性のあるバグ修正

#### リリースプロセス

1. **develop → main**: 安定版としてマージ
2. **タグ作成**: `git tag -a v1.2.0 -m "Release v1.2.0"`
3. **CHANGELOG.md 更新**: 変更内容を記録
4. **Docker イメージビルド**: 新版のコンテナ作成

### トラブルシューティング

#### よくある Git 問題

-   **コンフリクト**: `git mergetool` で解決
-   **コミット取り消し**: `git reset --soft HEAD~1`
-   **プッシュ前の修正**: `git commit --amend`
-   **ブランチ間違い**: `git cherry-pick` で移動

## AI アシスタント実行ルール

### 基本原則

1. **安全第一**: 本番環境に影響する変更は慎重に
2. **トレーサビリティ**: すべての変更を Git で追跡
3. **コミュニケーション**: 変更理由を明確に説明
4. **テスト重視**: 変更後は必ず動作確認

### 推奨アクション

1. 作業開始前に `git status` で現状確認
2. 適切なブランチ名で新しいブランチ作成
3. 段階的なコミットで変更履歴を明確化
4. コミットメッセージは規約に従い詳細に記述
5. プッシュ前に変更内容をレビュー

### 避けるべき行動

1. main ブランチへの直接コミット
2. 大量の変更を一度にコミット
3. 曖昧なコミットメッセージ
4. 強制プッシュ (`git push --force`)
5. 機密情報をコミットに含める

## プロジェクト固有の考慮事項

### セキュリティ

-   ダウンロード URL の検証
-   ファイルパス制限
-   悪意あるファイルの検出

### パフォーマンス

-   大容量ファイルのメモリ効率
-   同時ダウンロード数制限
-   プログレス更新頻度

### ユーザビリティ

-   エラーメッセージの分かりやすさ
-   進捗表示の正確性
-   設定の簡単さ

### 互換性

-   Python 3.8+ サポート
-   クロスプラットフォーム対応
-   ブラウザ互換性
