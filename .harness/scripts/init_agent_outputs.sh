#!/usr/bin/env bash
set -euo pipefail

TASK_DIR="${1:-}"
if [ -z "$TASK_DIR" ]; then
  if [ -f ".harness/.current-task" ]; then
    TASK_DIR="$(cat .harness/.current-task)"
  else
    echo "[ERROR] 请输入任务目录，或先设置 .harness/.current-task"
    exit 1
  fi
fi

OUT_DIR="$TASK_DIR/agent-outputs"
mkdir -p "$OUT_DIR"

for f in implement-result.md check-result.md debug-result.md finish-result.md; do
  if [ ! -f "$OUT_DIR/$f" ]; then
    cp ".harness/templates/agent-outputs/$f" "$OUT_DIR/$f"
  fi
done

echo "[OK] agent-outputs 模板已初始化: $OUT_DIR"
