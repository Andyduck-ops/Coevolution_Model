# Ops Manager（本地运维系统）

## 目标

把 `harness/references` 的系统管理知识落成可执行控制面，服务当前三个目标：
1. 搭建开工前运维系统；
2. 检查计划与 spec 设计质量；
3. 为多 Agent 调度与 review 审核提供机器可校验门禁。

## 方法论来源（已同化）

- `hook-based-enforcement`
- `failure-budget`
- `structured-escalation`
- `progressive-disclosure`
- `staleness-detection`
- `contract-replay-verification-gate`（本地轻量化）
- `pipeline-gate-canonicalization`（调度/审核一致性）

映射说明见：`.harness/spec/operations/methodology-cases.md`

## 控制面命令

- `bash .harness/scripts/opsctl.sh health`
- `bash .harness/scripts/opsctl.sh spec-audit`
- `bash .harness/scripts/opsctl.sh schedule-audit`
- `bash .harness/scripts/opsctl.sh review-audit`
- `bash .harness/scripts/opsctl.sh stale-gate`
- `bash .harness/scripts/opsctl.sh permission-audit`
- `bash .harness/scripts/opsctl.sh agent-audit`
- `bash .harness/scripts/opsctl.sh full-check`
- `bash .harness/scripts/opsctl.sh governance-check --strict`

## 关键合同文件

- `.harness/spec/operations/pipeline-contract.yaml`
- `.harness/spec/operations/review-gate.md`
- `.harness/spec/operations/command-permission-map.yaml`

## 产物

审计报告输出到：
- `.harness/tasks/<current-task>/evidence/ops_health_report.json`
- `.harness/tasks/<current-task>/evidence/spec_audit_report.json`
- `.harness/tasks/<current-task>/evidence/schedule_audit_report.json`
- `.harness/tasks/<current-task>/evidence/review_audit_report.json`
- `.harness/tasks/<current-task>/evidence/stale_gate_report.json`
- `.harness/tasks/<current-task>/evidence/permission_audit_report.json`
- `.harness/tasks/<current-task>/evidence/agent_watch_report.json`
