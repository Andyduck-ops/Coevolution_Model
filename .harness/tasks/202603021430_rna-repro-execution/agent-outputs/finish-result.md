# finish-result

## 端到端推进结论
- [x] 代码链路打通：I1-I5 均有可执行实现。
- [x] 测试链路打通：`pytest` 全部通过。
- [x] 质量门通过：`run_quality_gate.sh` 全绿。
- [x] 治理门通过：`governance-check --strict` 全绿。
- [x] 图表产物输出：Fig1-4 的 PNG/PDF 已生成。
- [x] 复现报告输出：`results/repro/repro_report.json`（passed=true）。

## 当前边界
- 当前复现报告以“产物完整性 + 管线可重复”为主。
- 已补“参考图保真门禁”能力，但当前默认阈值尚未通过。
- 已补“论文命题+消融”门禁能力，且 claim gate 已通过（E1-E5）。
- 已补“论文命题+消融”门禁能力，且 ablation gate 已通过（R1-R4）。
- 当前剩余阻断项：repro fidelity gate 未通过。
- 下一步聚焦：论文曲线级数值标定与 fidelity 提升。

## 建议下一迭代
1. 用 `scripts/search_fidelity_params.py` 做更大样本量 coarse search（>=30）并落地 top-k 参数。
2. 将论文原图数据点数字化，建立曲线级误差阈值并纳入保真门禁。
3. 对 `critical_stress` / `compute_spinodal` 引入论文参数反演与灵敏度报告。
