## 目的
このファイルは、このリポジトリでAIベースのコーディングエージェントが即戦力になるための「要点メモ」です。短く、変更箇所や参照ファイルを明示します。

### 簡易チェックリスト
- プロジェクト種別: Django アプリケーション（プロジェクトは `apps/` 配下）
- 主要アプリ: `accounts`, `main_app`（単純な Django アプリ構成）
- 設定: `apps/config/settings.py`（.env.{env} をルートで読み込む）
- 開発フロー: `python apps/manage.py migrate/runserver/test` を基本にする

## ビッグピクチャ（重要ポイント）
- コードベースは Django（settings は `apps/config/settings.py`）で、アプリケーション本体は `apps/` フォルダにある。
- `settings.py` は環境変数 `DJANGO_ENV`（`dev`/`prod` 等）から `.env.{env}` をプロジェクトルートで読み込む。つまり、ルートに `.env.dev` / `.env.prod` を配置すること。
- 開発時の DB は settings でデフォルト SQLite（`BASE_DIR / 'db.sqlite3'`）。一方、`docker-compose.yml` の production-like サービスは Postgres を使う（`db` サービス）。両者を混同しないこと。

## 重要なファイルと例
- `apps/config/settings.py` — .env 読み込みロジック、`SECRET_KEY` は必須で未設定時に例外を投げる。
- `apps/manage.py` — 管理コマンドのエントリポイント（ローカル起動、マイグレーション、テストはここ経由）。
- `docker-compose.yml` — 本番用のボリューム、nginx、Postgres を定義。ただし `web` の `build: ./backend` や `gunicorn fishlog.wsgi:application` の参照はレイアウトと齟齬があり得る（注意して検証すること）。
- `pyproject.toml` — 依存は最小限（例: `django>=6.0.3`, `python-dotenv`）。しかし `build-system` セクションがないため、依存は手動でインストールすることを推奨（下記参照）。

## 開発者ワークフロー（発見可能な最小コマンド）
※このプロジェクトは pyproject に依存リストがあるが、ビルド設定が不完全なため手動手順を記載する。

1. 仮想環境を作る
   - python -m venv .venv
   - source .venv/bin/activate
2. 依存を入れる（最小）
   - pip install "django>=6.0.3" python-dotenv
3. 環境ファイルを作る（ルート）
   - `.env.dev` を作り `DJANGO_ENV=dev`, `SECRET_KEY=...`, `DEBUG=True` などを設定
4. DB とマイグレーション
   - python apps/manage.py migrate
5. 開発サーバ起動
   - python apps/manage.py runserver
6. テスト実行
   - python apps/manage.py test

## プロジェクト固有の注意点・パターン
- settings の .env 読み込みは `Path(__file__).resolve().parent.parent.parent / f'.env.{env}'` でルートを期待する。
- ロケール/タイムゾーン: `LANGUAGE_CODE='ja'`, `TIME_ZONE='Asia/Tokyo'` — 日付/表示に関する変更はここを確認。
- アプリ毎のテストは `apps/<app>/tests.py` にある（単純な構成）。変更時はそのテストを先に走らせると効率的。

## インテグレーションポイント
- Docker: `docker-compose.yml`（`web`, `db`, `nginx`） — 本番系設定を含む。`env_file: .env.prod` を使う。
- nginx: `nginx/nginx.conf` が存在するが空のまま（テンプレートまたは未完）。nginx 設定を触る場合はここを更新して検証すること。

## 変更を行う際の実務ルール（AI向け短い指針）
- 変更は小さく。settings や env 関連を触る場合、`.env.dev` を用いたローカル検証を必ず行う。
- `docker-compose.yml` を編集する前に、参照先（`build` path や `wsgi` モジュール名）がこのリポジトリの構造と一致しているか確認する。
- 変更後は `python apps/manage.py test` を実行して既存テストが通ることを確認すること。

## 追加情報をリクエストしてください
不明点（例: 本番の Docker ビルドパス、期待する wsgi モジュール名、.env の必須キー一覧など）があれば指定してください。これらを反映して短い更新を行います。

--
（このファイルはリポジトリ内から自動マージ用に簡潔に保たれています。追記希望をどうぞ）
