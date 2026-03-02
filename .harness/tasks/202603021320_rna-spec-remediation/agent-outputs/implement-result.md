# implement-result

## 变更摘要
- 新增权限阶梯与结构化升级规范（operation spec）。
- 新增 agent-outputs 标准模板与初始化脚本。
- 新增 E2E smoke 链路（参数加载→最小 ODE→产图→摘要文件）。

## 涉及文件
- `.harness/spec/operations/permission-ladder.md`
- `.harness/spec/operations/reference-sync.md`
- `.harness/templates/agent-outputs/*.md`
- `.harness/scripts/init_agent_outputs.sh`
- `src/rna_llps/config.py`
- `src/rna_llps/models/minimal_ode.py`
- `src/rna_llps/pipeline/smoke.py`
- `scripts/e2e_smoke.py`

## 实现证据
- 命令：`bash .harness/scripts/e2e_smoke.sh`
- 结果：生成 `results/smoke/smoke_timeseries.npz`、`figures/smoke/smoke_trajectory.png`

## 风险与限制
- 当前 ODE 为 smoke 骨架模型，不等同论文最终方程。
- 后续需将 P0/P1 数学条目映射到正式模型实现。
