# Tasks（论文命题 + 消融实验）

## 目标
将论文核心命题（E1-E5）与反驳/消融实验（R1-R4）纳入统一 DAG，形成“实现-检查-review”闭环。

## 阶段任务清单

### Plan
- [ ] P3_claim_mapping：冻结命题与反驳矩阵（`planning/ablation-matrix.yaml`）

### Implement
- [ ] I6_claim_runner：实现命题实验执行器 `scripts/run_claim_experiments.py`
- [ ] I7_ablation_runner：实现反驳/消融执行器 `scripts/run_ablation_experiments.py`
- [ ] I8_report_merge：合并报告并生成 `paper_validation_report.json`

### Check
- [ ] C3_claim_gate：命题实验严格门禁（`--strict`）
- [ ] C4_ablation_gate：消融实验严格门禁（`--strict`）
- [ ] C5_integrated_gate：质量门 + 治理门 + 论文门禁联合通过

### Debug
- [ ] D3_claim_fix：修复命题门禁失败
- [ ] D4_ablation_fix：修复消融门禁失败

### Review
- [ ] R1_peer_review：独立审核（implementer != reviewer）
- [ ] review-audit 通过

### Finish
- [ ] F2_paper_validation_release：输出最终论文验证报告与README更新

## 必交付文件
- `results/repro/claim_report.json`
- `results/repro/ablation_report.json`
- `results/repro/paper_validation_report.json`

## 阻断与升级
- 同类失败 >=3 次：升级人工
- claim 指标冲突且无法自动裁决：升级人工
