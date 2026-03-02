# Figure Reproduction Specifications

## 目标

可重复生成主文 Fig1-4 与 SI Fig1-5（后续扩展）。

## 必备函数

- `solve_full_ode()`
- `critical_stress()`
- `compute_spinodal()`
- `solve_post_segregation()`

## 必备机制

1. 参数扫描模板（含种子、范围、输出路径）。
2. 图表输出双格式：PDF + PNG。
3. 每张图有独立可运行入口（脚本或 notebook）。
4. 关键图（Fig1B）支持相线 quiver 可视化。
