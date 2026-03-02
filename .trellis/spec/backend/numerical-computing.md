# 数值计算规范

## ODE 求解器

### 主力求解器

- 统一入口：`scipy.integrate.solve_ivp`
- 默认：`method="Radau"`
- 备选：`method="BDF"`
- 非刚性探索：`method="RK45"`（仅子问题）

### 为什么选 RADAU

本系统存在**时间尺度分离** (`alpha, kappa >> mu_x, mu_y`)，属于 stiff ODE。  
隐式方法（RADAU/BDF）对该类问题更稳定，显式方法（RK45）会因步长过小而显著变慢。

参考: Städter et al., *Scientific Reports* (2021)

### 备选方法

| 方法 | 何时使用 |
|------|----------|
| `RADAU` | **默认选择**，大多数场景 |
| `BDF` | RADAU 收敛困难时 |
| `RK45` | 非刚性局部分析 |

### 误差控制标准

| 场景 | rtol | atol |
|------|------|------|
| 常规模拟 | `1e-8` | 向量化 `atol=[1e-10,1e-10,1e-12,1e-12]` |
| 参数扫描（速度优先） | `1e-6` | `1e-8` |
| 高精度验证 | `1e-12` | `1e-14` |

> 约束：多尺度变量必须支持 **atol 向量化**，禁止单标量 atol 覆盖全部分量。

---

## 解析 Jacobian（强烈建议）

- 对核心 4 变量系统提供 `jac_full_system(t, y, params)`。
- `solve_ivp(..., jac=jac_full_system)` 作为默认启用路径。
- 目标：提升收敛稳定性与求解效率（典型可提升 2-5x）。

最小接口：

```python
# returns shape (4,4)
def jac_full_system(t: float, y: np.ndarray, params: dict) -> np.ndarray: ...
```

---

## 事件检测（事件/终止条件）

必须实现以下 **事件**（event）函数：

1. `event_spinodal_crossing(t, y, params)`
   - 检测 `chi_RP_eff - chi_critical = 0` 的穿越点。
2. `event_quasi_steady(t, y, params)`
   - 检测 `||dy/dt|| < tol` 的准稳态到达。

推荐设置：

- `event.direction = 0`
- `event.terminal = False`（扫描）或 `True`（单次求临界点）

---

## 稳态求解

### 标量方程 `X` 的稳态

- 使用 `scipy.optimize.brentq` 求解隐式稳态条件。
- 搜索区间 `[0, X_upper]`，`X_upper` 由渐近标度估计。
- 当 `n>1` 时，在方程残差定义中显式使用 `B_n`，禁止退化为 `B`。

### 完整 4 变量系统的稳态

- 初值来自时间积分末态；再调用 `scipy.optimize.root` 微调。
- 收敛失败时记录日志并回退到高精度时间积分方案。

---

## 参数管理

### YAML 配置结构

- 默认参数：`configs/default_params.yaml`
- 参数分组：
  - 动力学：`mu_x, mu_y, alpha, beta, kappa, K_R, K_P, V_x, V_y, gamma, delta_0, E, n`
  - 热力学：`v_R, v_P, chi_RR, chi_PP, chi_0, epsilon, k_BT`

### 参数加载规范

- 启动时校验必填项；缺失即报错退出。
- 记录加载配置的绝对路径与 hash（保证可追踪）。

### 参数覆盖（用于参数扫描）

- CLI 覆盖优先于 YAML。
- 每次扫描写入一份最终参数快照（JSON）。

---

## 数值稳定性补丁

- `Π_P = exp(epsilon*x_bar*y_bar/k_BT)` 在实现中使用对数域防溢出：
  - `log_pi = epsilon*x_bar*y_bar/k_BT`
  - `log_pi` 裁剪到 `[-60, 60]`
  - 再执行 `np.exp(log_pi)`

---

## 数值输出规范

- 时间序列数据：保存为 NumPy `.npz`
- 参数扫描结果：保存为 `.npz` 或 `.csv`
- 每次模拟记录：参数文件、求解器设置、运行时间、事件触发信息
- 文件命名：`{module}_{description}_{date}.npz`
