# P0/P1 方程-代码-测试追踪表（基线）

> 状态：2026-03-02，进入执行前冻结。

| ID | 规范条目 | 目标实现函数/模块 | 目标测试 | 当前状态 |
|---|---|---|---|---|
| EQ-P0-01 | `V_x, V_y` 参与特征方差与 A/λ 计算 | `src/rna_llps/models/scalar_dynamics.py::compute_variance_terms` | `tests/test_scalar_dynamics.py::test_variance_terms_use_vx_vy` | done |
| EQ-P0-02 | 热力学参数组 `v_R,v_P,chi_RR,chi_PP,chi_0,epsilon,k_BT` | `src/rna_llps/thermo/flory_huggins.py` | `tests/test_flory_huggins.py` | done |
| EQ-P0-03 | 两相辅助链 `Θ_R -> W^I/W^II -> P_eff -> A_eff -> X_loc` | `src/rna_llps/models/post_segregation.py` | `tests/test_post_segregation.py` | done |
| EQ-P1-01 | `B_n = delta_0 * E * gamma^n` 下标/幂次规则 | `src/rna_llps/models/scalar_dynamics.py::compute_bn` | `tests/test_scalar_dynamics.py::test_bn_power_rule` | done |
| EQ-P1-02 | `Π_P = exp(epsilon*x*y/k_BT)` 数值稳定策略 | `src/rna_llps/thermo/flory_huggins.py::partition_coeff_logsafe` | `tests/test_flory_huggins.py::test_partition_coeff_logsafe` | done |
| NUM-P1 | 解析 Jacobian + 事件检测 + 回退策略 | `src/rna_llps/solvers/ode_wrappers.py` | `tests/test_ode_wrappers.py` | done |
| FIG-P1 | `solve_full_ode()` 包装 | `src/rna_llps/solvers/ode_wrappers.py::solve_full_ode` | `tests/test_ode_wrappers.py::test_solve_full_ode_runs` | done |
| FIG-P1 | `critical_stress()` 包装 | `src/rna_llps/analysis/stability.py::critical_stress` | `tests/test_stability_analysis.py::test_critical_stress_exists` | done |
| FIG-P1 | `compute_spinodal()` 包装 | `src/rna_llps/analysis/stability.py::compute_spinodal` | `tests/test_stability_analysis.py::test_compute_spinodal_exists` | done |
| FIG-P1 | `solve_post_segregation()` 包装 | `src/rna_llps/models/post_segregation.py::solve_post_segregation` | `tests/test_post_segregation.py::test_solve_post_segregation_runs` | done |

## 规则
1. 每个规范条目至少绑定 1 个函数 + 1 个测试。
2. 任何“pending -> done”必须伴随可执行测试通过记录。
3. 若论文符号定义冲突，必须触发结构化升级，不得擅自猜测。
