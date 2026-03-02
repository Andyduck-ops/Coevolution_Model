# Review Checklist（Claims + Ablation）

## 角色约束
- [ ] `task.json.agents.implementer != task.json.agents.reviewer`
- [ ] `evidence/review_meta.json` 字段完整且与 `task.json.agents` 对齐

## 报告一致性
- [ ] `claim_report.json` 存在且可解析
- [ ] `ablation_report.json` 存在且可解析
- [ ] `paper_validation_report.json` 合并逻辑正确（含 pass/fail 与原因）

## 指标判据
- [ ] E1 单调律判据满足
- [ ] E2 稳定性/无滞后判据满足
- [ ] E3 解耦判据满足
- [ ] E4 crossing 判据满足
- [ ] E5 post-seg 加速判据满足
- [ ] R1-R4 反驳实验输出完整并可解释

## 流水线门禁
- [ ] `bash .harness/scripts/run_quality_gate.sh` 通过
- [ ] `bash .harness/scripts/opsctl.sh governance-check --strict` 通过
- [ ] `bash .harness/scripts/opsctl.sh review-audit` 通过
