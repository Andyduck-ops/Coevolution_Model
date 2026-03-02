# Agent Assignment（治理流水线）

## 角色与职责

| 角色 | 阶段 | 关键输出 | 强制门禁 |
|---|---|---|---|
| plan-agent | plan | `prd.md`、`task.json`、`planning/execution-dag.yaml`、`planning/experiment-dag-claims-ablation.yaml` | `schedule-audit` |
| implement-agent | implement | `agent-outputs/implement-result.md` + 代码/测试变更 | 单元测试 + lint |
| ablation-agent | implement | `scripts/run_ablation_experiments.py` + `results/repro/ablation_report.json` | `C4_ablation_gate` |
| claim-agent | implement | `scripts/run_claim_experiments.py` + `results/repro/claim_report.json` | `C3_claim_gate` |
| check-agent | check | `agent-outputs/check-result.md`（6项命令全量） | `run_quality_gate.sh` |
| gpt-5.2-xhigh-reviewer | review | `evidence/review_meta.json` + 结论 | `review-audit` |
| ops-agent | governance | 统一审计报告写入 `evidence/*.json` | `opsctl governance-check --strict` |
| watch-agent | watch | `.watch_state.json` + stop/continue 决策 | `agent-audit` |

## 分配规则
1. 实现人与审核人必须不同（`implementer != reviewer`）。
2. check 阶段必须执行并记录六条验证命令：lint/test/build/e2e/hook replay/ops full-check。
3. 任何阻断失败进入 debug，按同类失败预算（<=3）推进。
4. `governance-check --strict` 未通过时，禁止 finish。

## 升级模板

```md
## 需要你决策
- 当前阻塞:
- 已尝试策略:
- 方案A（推荐）:
- 方案B:
- 风险与代价:
- 默认执行（若你未回复）:
```
