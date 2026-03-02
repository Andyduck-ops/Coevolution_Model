# 方程-代码对应参考

> 编码时查阅：论文方程编号 → 对应函数。  
> 目标：避免“只有标题没有可实现定义”的空转规范。

## 1. 核心 4变量 ODE 系统

**论文 Eqs. (1)-(4)**

设状态向量 `y = [R, P, x_bar, y_bar]`，通式写作：

- `dR/dt = F_R(R, P, x_bar, y_bar; params)`
- `dP/dt = F_P(R, P, x_bar, y_bar; params)`
- `dx_bar/dt = F_x(R, P, x_bar, y_bar; params)`
- `dy_bar/dt = F_y(R, P, x_bar, y_bar; params)`

→ 函数: `models/core_ode.py::rhs_full_system(t, y, params)`

---

## 2. 降维标量动力学

**论文 Eq. (9)**（`n=1` 特例）

- `dX/dτ = A*(αβ + B)/(1 + X) - 1 - B*X`

**论文 Eq. (9) 一般形式**（任意 `n`）

- `dX/dτ = A*(αβ + B_n)/(1 + X)^n - 1 - B_n*X`

> 下标约定：`B_n = δ0 * E * γ^n`，下标 `n` 显式表示 Hill 阶数依赖，禁止把 `B` 与 `B_n` 混用。

→ 函数: `models/scalar_dynamics.py::rhs_scalar(tau, X, A, B_n, alpha_beta, n=1)`

---

## 3. 复合参数定义（P0）

| 符号 | 定义 | 物理含义 |
|------|------|----------|
| `A` | `V_x * K_P * λ / μ_x` | 有效反馈强度 |
| `B_n` | `δ0 * E * γ^n` | 应激注入强度（n 阶） |
| `λ` | `κ * V_y * K_R / μ_y` | 肽响应系数 |
| `X` | `γ * K_P * λ * x_bar^2` | 无量纲耦合强度 |
| `τ` | `μ_x * t` | 无量纲时间 |

> P0 补充：`V_x`、`V_y` 必须作为一级参数出现在 `params` 中，不允许硬编码。

→ 函数: `utils/parameters.py::compute_composite_params(params)`

---

## 4. 稳态条件

**论文 Eq. (10) (`n=1`)**

- `0 = A*(αβ + B)/(1 + X*) - 1 - B*X*`

**一般形式 (`n>=1`)**

- `0 = A*(αβ + B_n)/(1 + X*)^n - 1 - B_n*X*`

→ 函数: `analysis/stability.py::solve_steady_state(A, B_n, alpha_beta, n=1)`

---

## 5. 灵敏度

**论文 Eq. (14)**

- `S_B = dX*/dB`

实现时写成隐函数导数形式，避免直接差分噪声放大。

→ 函数: `analysis/stability.py::sensitivity_dXdB(X_star, B)`

---

## 6. 自适应势函数

**论文 Section III.B**

- `U(X) = - ∫ G(X) dX + C`
- 其中 `G(X) = dX/dτ`，并取积分常数 `C` 使 `U(X*) = 0`。

→ 函数: `analysis/stability.py::potential_U(X, A, B_n, alpha_beta, n=1)`

---

## 7. Flory-Huggins 自由能（P0）

**论文 Eq. (31) / Appendix D**

- `f/(k_BT) = φ_R/(v_R) ln φ_R + φ_P/(v_P) ln φ_P + ... + χ_RR φ_R^2 + χ_PP φ_P^2 + χ_RP_eff φ_R φ_P`

必需参数组：
- `v_R`, `v_P`
- `χ_RR` (`chi_RR`), `χ_PP` (`chi_PP`)
- `k_BT`（代码可写 `kBT`，但参数表字段必须保留 `k_BT`）

→ 函数: `thermo/flory_huggins.py::free_energy(phi_R, phi_P, chi_RR, chi_PP, chi_RP_eff, v_R, v_P, k_BT)`

---

## 8. 有效异型作用参数（P0）

**论文 Eq. (32)**

- `χ_RP_eff = χ_0 - ε * x_bar * y_bar / k_BT`

参数：`chi_0`, `epsilon`, `k_BT`。

→ 函数: `thermo/flory_huggins.py::chi_RP_eff(x_bar, y_bar, chi_0, epsilon, k_BT)`

---

## 9. Spinodal 条件

**论文 Eq. (33)**

- `det(Hessian(f)) = 0`
- 常用实现：求 `χ_critical(φ_R, φ_P, χ_RR, χ_PP, v_R, v_P)`，再比较 `χ_RP_eff`。

→ 函数: `thermo/flory_huggins.py::chi_critical(phi_R, phi_P, chi_RR, chi_PP, v_R, v_P)`

---

## 10. 两相后分离动力学（P0）

**论文 Eq. (39) / Appendix F**

### 10.1 分配系数

- `Π_P = exp(ε * x_bar * y_bar / k_BT)`

> 数值稳定性：实现中用 `log_Π_P = ε*x_bar*y_bar/k_BT`，并对 `log_Π_P` 做区间裁剪（如 `[-60, 60]`），避免指数溢出。

### 10.2 两相辅助函数链（Fig4 必需）

- `Θ_R`：RNA 在两相间的分配函数
- `W^I`, `W^II`：相 I / II 的权重函数
- `P_eff`：有效肽浓度
- `A_eff`：后分离有效反馈参数
- `X_loc`：局部耦合强度

建议依赖链：

1. `Π_P` → 2. `Θ_R` → 3. `W^I/W^II` → 4. `P_eff` → 5. `A_eff` → 6. `X_loc`

→ 主函数: `models/post_segregation.py::rhs_two_phase(tau, X, params, f)`
→ 辅助函数: `models/post_segregation.py::{partition_coefficient, theta_r, phase_weights, p_eff, a_eff, x_loc}`

---

## 参数映射总表（实现约束）

- 动力学：`mu_x, mu_y, alpha, beta, kappa, K_R, K_P, V_x, V_y, gamma, delta_0, E, n`
- 热力学：`v_R, v_P, chi_RR, chi_PP, chi_0, epsilon, k_BT`

任一缺失都视为 **spec 阻断项**。
