# Development Workflow (RNA LLPS)

> Auto-generated + adapted from /home/eric/harness for this project.

## Core Principles

1. **Harness First** — 遇到反复失败先修执行环境（hooks / tests / commands），再修实现。
2. **Mechanical Enforcement** — 能被命令验证的，不只写在文档里。
3. **Spec Before Code** — 先补齐数学与复现规范，再进入大规模实现。
4. **Evidence-Based Iteration** — 每次实现都要有可执行验证证据。

## Verification Commands

- **Test**: `.venv/bin/python -m pytest -q`
- **Lint**: `.venv/bin/python -m ruff check src tests`
- **Build**: `.venv/bin/python -m compileall -q src`
- **E2E Smoke**: `bash .harness/scripts/e2e_smoke.sh`
- **Hook Replay**: `bash .harness/scripts/hook_replay.sh`
- **Ops Full Check**: `bash .harness/scripts/opsctl.sh full-check`
- **Governance Check**: `bash .harness/scripts/opsctl.sh governance-check --strict`

## Pipeline Stages

```text
plan → implement → check → [debug ≤3] → finish
```

| Stage | Agent 目标 | 必要输出 |
|---|---|---|
| plan | 固化需求与边界 | `prd.md`, 成功标准, 验证命令 |
| implement | 开发/文档修补 | 代码变更 + `agent-outputs/implement-result.md` |
| check | 运行验证并审计 | `agent-outputs/check-result.md` |
| debug | 失败修复（最多 3 次） | `agent-outputs/debug-result.md` |
| finish | 交付收束 | 变更摘要 + 风险 + 下一步 |

## Permission Ladder

详见：`.harness/spec/operations/permission-ladder.md`

- L1: 只读分析
- L2: 验证命令
- L3: 修改代码
- L4: 外部操作（推送/发布）

## Structured Escalation Rules

触发任一条件即升级求助：
1. 同类失败累计 2 次，第三次前必须换策略；
2. 缺失关键上下文；
3. 需要 L4 外部操作；
4. 多方案无法自动裁决。

## Ops Control Plane

- health: `bash .harness/scripts/opsctl.sh health`
- spec audit: `bash .harness/scripts/opsctl.sh spec-audit`
- schedule audit: `bash .harness/scripts/opsctl.sh schedule-audit`
- review audit: `bash .harness/scripts/opsctl.sh review-audit`
- stale gate: `bash .harness/scripts/opsctl.sh stale-gate`
- permission audit: `bash .harness/scripts/opsctl.sh permission-audit`
- agent audit: `bash .harness/scripts/opsctl.sh agent-audit`
- governance check: `bash .harness/scripts/opsctl.sh governance-check --strict`

## Current Project Focus (2026-03-02)

1. 先修补 RNA 模型 spec 的 P0 缺口（参数、两相辅助链、依赖版本）。
2. 再搭脚手架并逐步实现 ODE/热力学/图表复现模块。
3. 以论文复现为目标，执行端到端可验证流水线。
