#!/usr/bin/env bash
set -euo pipefail

# このスクリプトのディレクトリ → プロジェクトルートへ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# 仮想環境があれば有効化
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
else
  echo "[INFO] .venv が見つかりませんでした。グローバルの python3 を使用します。"
fi

# プロジェクトルートを PYTHONPATH に追加（-m 実行の保険）
export PYTHONPATH="${PYTHONPATH:-}:${PROJECT_ROOT}"

# ログレベルを環境変数から上書き可能に
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# 実行（必要に応じて引数をそのまま渡す）
exec python3 -m batch.run_crawl "$@"