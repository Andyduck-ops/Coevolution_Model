# PRD: RNA 论文复现执行（P0/P1→Fig1-4）

## 目标
在已完成 harness 治理闭环的基础上，进入论文复现主线落地：
1. 将 P0/P1 规范转成可执行代码与测试；
2. 建立 ODE/热力学/两相链路的稳定求解与审计；
3. 形成 Fig1-4 可重复产物（PNG+PDF）与复现报告。

## Success Criteria
- SC-1: `docs/repro/p0_p1_traceability.md` 完成方程→函数→测试追踪。
- SC-2: `configs/solver_contract.yaml` 明确 Jacobian/事件/回退策略并有测试守护。
- SC-3: 四个包装函数可调用：`solve_full_ode()`、`critical_stress()`、`compute_spinodal()`、`solve_post_segregation()`。
- SC-4: 生成 `figures/paper/fig1-fig4` 的 PNG 与 PDF 产物。
- SC-5: `results/repro/repro_report.json` 输出关键指标偏差与是否通过。
- SC-6: `bash .harness/scripts/opsctl.sh governance-check --strict` 全绿。

## Boundaries
- Always: 先以可验证最小实现推进，再迭代精细化物理模型。
- Ask: 遇到论文参数定义歧义（特别是两相链与临界条件）必须结构化升级。
- Never: 跳过 check/review 阶段直接宣布“复现成功”。

## Permission Ladder
- L1: 读取规范、论文、历史产物
- L2: 运行验证命令（lint/test/build/e2e/ops）
- L3: 修改代码、脚本、配置、测试
- L4: 外部操作（push/release/远程发布）

## Structured Escalation
触发条件（任一成立）：
1. 同类失败达到第 3 次前；
2. 论文符号/参数不完整导致无法实现；
3. 需要 L4 外部动作；
4. 多方案无法自动裁决。

升级输出必须含：阻塞点、已尝试策略、A/B 方案、风险、默认建议。

## Verification Commands
- `.venv/bin/python -m ruff check src tests`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m compileall -q src`
- `bash .harness/scripts/e2e_smoke.sh`
- `bash .harness/scripts/hook_replay.sh`
- `bash .harness/scripts/opsctl.sh full-check --strict`
- `bash .harness/scripts/opsctl.sh governance-check --strict`
