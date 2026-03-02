# Backend Specifications (RNA LLPS)

## 技术底线

- Python 3.10+
- 使用 `src/` layout
- 参数配置集中在 `configs/*.yaml`
- 所有核心函数需要单元测试（正常/边界/异常）

## 数值计算要求

1. 刚性 ODE 默认 `solve_ivp(method="Radau")`，备选 `BDF`。
2. 默认误差控制：`rtol=1e-8`；`atol` 按变量量纲向量化。
3. 实现解析 Jacobian（至少对 4 变量主系统给出）。
4. 关键事件检测：spinodal 穿越与稳态收敛事件。

## 代码与规范来源

- 现有规范：`.trellis/spec/backend/`
- 本 Harness 文档用于执行时注入，强调“必须落实到命令可验证”。
