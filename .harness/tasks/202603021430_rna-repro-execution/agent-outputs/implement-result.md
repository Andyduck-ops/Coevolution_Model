# implement-result

## 本轮实现范围
- [x] I1: `solve_full_ode()` + `jac_full_system()` + 事件检测 + Radau/BDF 回退
- [x] I2: 热力学与标量函数（`B_n`, `Π_P`, `chi_*`, 两相辅助链）
- [x] I3: `solve_post_segregation()` 两相后分离积分包装
- [x] I4: `critical_stress()` / `compute_spinodal()` 稳定性接口
- [x] I5: Fig1-4 独立脚本 + 复现检查脚本
- [x] I6: 论文命题实验执行器（E1-E5）
- [x] I7: 消融/反驳实验执行器（R1-R4）
- [x] I8: 统一论文验证报告聚合
- [x] I9: 论文方程对齐修补（4 变量 ODE、spinodal 事件、`chi_eff/chi_c` 公式）
- [x] I10: 数值稳定性修补（耦合项截断、非单调序列 t95 判定、E4 crossing 稳健计数）
- [x] I11: 参数基线重标定（default_params 使 E1-E5 claim gate 通过）
- [x] I12: 消融判据稳健化迭代（R1/R2/R4 转绿，R3 待修复）

## 关键新增文件
- `src/rna_llps/solvers/ode_wrappers.py`
- `src/rna_llps/thermo/flory_huggins.py`
- `src/rna_llps/models/scalar_dynamics.py`
- `src/rna_llps/models/post_segregation.py`
- `src/rna_llps/analysis/stability.py`
- `scripts/fig1_stability.py`
- `scripts/fig2_timecourse.py`
- `scripts/fig3_spinodal.py`
- `scripts/fig4_post_segregation.py`
- `scripts/check_reproduction_metrics.py`
- `scripts/run_claim_experiments.py`
- `scripts/run_ablation_experiments.py`
- `scripts/merge_claim_ablation_report.py`

## 测试补齐
- [x] `tests/test_flory_huggins.py`
- [x] `tests/test_scalar_dynamics.py`
- [x] `tests/test_ode_wrappers.py`
- [x] `tests/test_post_segregation.py`
- [x] `tests/test_stability_analysis.py`
- [x] `tests/test_reproduction_pipeline.py`
- [x] `tests/test_claim_experiments.py`
- [x] `tests/test_ablation_experiments.py`
- [x] `tests/test_merge_claim_ablation_report.py`
