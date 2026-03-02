# Ops Manager（本地运维系统）

## 目标

把 `harness/references` 的系统管理知识落成可执行控制面，服务当前两个核心目标：
1. 搭建开工前运维系统；
2. 检查计划与 spec 设计质量。

## 方法论来源（已同化）

- `hook-based-enforcement`
- `failure-budget`
- `structured-escalation`
- `progressive-disclosure`
- `staleness-detection`
- `contract-replay-verification-gate`（本地轻量化）

映射说明见：`.harness/spec/operations/methodology-cases.md`

## 控制面命令

- `bash .harness/scripts/opsctl.sh health`
  - 检查 hook、任务状态、运行环境、命令配置是否完整。
- `bash .harness/scripts/opsctl.sh spec-audit`
  - 检查 `.trellis/spec` 是否满足当前 P0/P1 审查要求。
- `bash .harness/scripts/opsctl.sh full-check`
  - 先跑 health，再跑 spec-audit。
- `bash .harness/scripts/hook_replay.sh`
  - 回放关键 hook 事件载荷，验证 Hook 链路真实可运行。

## 产物

审计报告输出到：
- `.harness/tasks/<current-task>/evidence/ops_health_report.json`
- `.harness/tasks/<current-task>/evidence/spec_audit_report.json`
