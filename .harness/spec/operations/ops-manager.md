# Ops Manager（本地运维系统）

## 目标

把 `harness/references` 的系统管理知识落成可执行控制面，服务当前两个核心目标：
1. 搭建开工前运维系统；
2. 检查计划与 spec 设计质量。

## 控制面命令

- `bash .harness/scripts/opsctl.sh health`
  - 检查 hook、任务状态、运行环境、命令配置是否完整。
- `bash .harness/scripts/opsctl.sh spec-audit`
  - 检查 `.trellis/spec` 是否满足当前 P0/P1 审查要求。
- `bash .harness/scripts/opsctl.sh full-check`
  - 先跑 health，再跑 spec-audit。

## 产物

审计报告输出到：
- `.harness/tasks/<current-task>/evidence/ops_health_report.json`
- `.harness/tasks/<current-task>/evidence/spec_audit_report.json`
