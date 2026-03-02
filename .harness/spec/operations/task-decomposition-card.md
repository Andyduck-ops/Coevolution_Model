# 任务拆分方法卡（RNA LLPS 仓库版）

> 目的：把“任务拆分”从经验动作变成可审计、可执行、可升级的流水线合同。  
> 适用范围：本仓库 `.harness/tasks/*` 下的研发任务（含 spec 修补、实现、验证、审核）。

## 1. 拆分维度

| 维度 | 拆分问题 | 本仓库表达方式 | 通过标准 |
|---|---|---|---|
| 阶段维度 | 任务处于哪个阶段？ | `plan -> implement -> check -> [debug<=3] -> finish` | 阶段必需工件齐全 |
| 目标维度 | 该阶段要产出什么？ | `prd.md`、`task.json`、`agent-outputs/*.md`、`evidence/*.json` | 工件存在且达到最小内容长度 |
| 风险维度 | 哪些失败会阻断推进？ | 质量门失败、spec 审计失败、审核独立性失败、知识陈旧 | 阻断项为 0 |
| 权限维度 | 当前动作需要哪级权限？ | L1 只读、L2 验证、L3 修改、L4 外部操作 | 权限映射命令可审计 |
| 证据维度 | 如何证明“做过且做对”？ | 审计报告 + 阶段结果 + 审核元数据 | 证据链可回放、可对账 |

## 2. 依赖关系表达

### 2.1 标准表达（推荐 YAML）

```yaml
contract_id: RNA-OPS-PIPELINE
stages:
  - id: plan
    requires: []
    required_artifacts: [prd.md, task.json]

  - id: implement
    requires: [plan]
    required_artifacts: [agent-outputs/implement-result.md]

  - id: check
    requires: [implement]
    required_artifacts:
      - agent-outputs/check-result.md
      - evidence/ops_health_report.json
      - evidence/spec_audit_report.json

  - id: debug
    requires: [check]
    optional: true

  - id: finish
    requires: [check]
    optional: true

stop_conditions:
  - id: stop_ready
    rule: "required artifacts all pass and no critical findings"
  - id: escalate_human
    rule: "same failure class >= 3"
```

### 2.2 关系语义

- `requires`：前置阶段依赖，任何未满足依赖都会在 `schedule-audit` 报错。  
- `required_artifacts`：阶段完成的客观证据，不允许以口头结论替代。  
- `optional: true`：可选阶段，但若执行则必须满足该阶段工件约束。  
- `stop_conditions`：定义“何时收敛”和“何时升级”，避免无限循环。

## 3. 失败预算（Failure Budget）

| 失败类 | 预算 | 触发位置 | 超预算动作 |
|---|---:|---|---|
| 同类 debug 失败 | 3 次 | `quality-gate` | 立即阻断并升级人工决策 |
| 总迭代次数 | 20 次 | `quality-gate` | 触发安全停机，禁止继续自动循环 |
| 单次验证命令失败 | 0 容忍 | `check` 阶段 | 立即阻断，进入 debug/升级流程 |
| 关键审计失败（spec/review/schedule/stale） | 0 容忍 | `opsctl governance-check --strict` | 禁止进入 finish |
| 审核独立性失败（implementer=reviewer） | 0 容忍 | `review-audit` | 阻断并要求更换 reviewer |

补充规则：
- 预算按“同类失败”累计，不因换人或中间插入其他步骤自动清零。  
- `debug >= 2` 时，第 3 次前必须换策略（不能同策略硬重试）。

## 4. 升级规则（Structured Escalation）

### 4.1 升级触发

出现以下任一条件，必须升级：
1. 同类失败达到 2 次，准备进入第 3 次尝试。  
2. 缺失关键上下文，无法可靠裁决（如论文参数定义不全）。  
3. 需要 L4 外部操作（推送、发布、外部 API 写入）。  
4. 多方案存在显著权衡，系统无法自动裁决。

### 4.2 升级输出格式（禁止开放式“我该怎么办”）

```md
## 需要你决策

- 当前阻塞:
- 已尝试策略:
- 方案 A（推荐）:
- 方案 B:
- 风险与代价:
- 若你未回复的默认执行:
```

要求：必须给出推荐项和默认项，避免把认知负担完全转交给人工。

## 5. 证据产物清单（Evidence Checklist）

### 5.1 阶段工件（最小集）

| 阶段 | 必需工件 |
|---|---|
| plan | `prd.md`, `task.json` |
| implement | `agent-outputs/implement-result.md` |
| check | `agent-outputs/check-result.md`, `evidence/ops_health_report.json`, `evidence/spec_audit_report.json` |
| debug（可选） | `agent-outputs/debug-result.md` |
| finish（可选） | `agent-outputs/finish-result.md` |

### 5.2 审计证据（治理最小集）

- `evidence/ops_health_report.json`
- `evidence/spec_audit_report.json`
- `evidence/schedule_audit_report.json`
- `evidence/review_audit_report.json`
- `evidence/stale_gate_report.json`
- `evidence/permission_audit_report.json`
- `evidence/agent_watch_report.json`
- `evidence/review_meta.json`

### 5.3 状态与追踪证据（建议保留）

- `.state.json`（迭代/失败预算状态）
- `.watch_state.json`（任务监控快照）
- `implement.jsonl` / `check.jsonl` / `debug.jsonl`（过程日志）

## 6. 落地用法（执行顺序）

1. 在任务目录建立 `prd.md` + `task.json`，明确完成标准。  
2. 按 `pipeline-contract.yaml` 建立阶段依赖与工件清单。  
3. 每次进入 `check` 前运行完整验证命令集（lint/test/build/e2e/hook replay/ops）。  
4. 任一阻断失败进入 `debug`，按失败预算计数，禁止无限重试。  
5. 达到升级条件时使用结构化升级模板请求决策。  
6. 仅当阶段工件与治理证据都通过时进入 `finish`。

## 7. 来源映射（本仓库 + 上游模式）

### 本仓库落地来源

- `.harness/workflow.md`
- `.harness/spec/operations/pipeline-contract.yaml`
- `.harness/spec/operations/permission-ladder.md`
- `.harness/spec/operations/review-gate.md`
- `.harness/spec/operations/methodology-cases.md`
- `.harness/scripts/ops_manager.py`
- `.harness/hooks/quality-gate.py`

### 上游治理模式来源

- `/home/eric/harness/references/lanes/engineering/patterns/agent-lifecycle/failure-budget.md`
- `/home/eric/harness/references/lanes/engineering/patterns/agent-lifecycle/structured-escalation.md`
- `/home/eric/harness/references/lanes/engineering/patterns/pipeline-governance/pipeline-gate-canonicalization.md`
- `/home/eric/harness/references/lanes/engineering/patterns/fullstack-engineering/contract-replay-verification-gate.md`
- `/home/eric/harness/references/lanes/engineering/patterns/evidence-governance/artifact-retention-reconciliation-governance.md`
