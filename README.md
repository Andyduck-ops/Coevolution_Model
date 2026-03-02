# RNA LLPS Coevolution Reproduction

面向论文 **A Coevolution Model of Stress-Driven RNA–Peptide Functional Enhancement and Liquid–Liquid Phase Separation** 的本地复现工程。

## 当前阶段

- [x] 搭建 `.harness/` 执行环境（hooks + quality gate + task context）
- [x] 固化工程依赖版本（`pyproject.toml`）
- [x] 建立最小可运行 Python 脚手架（`src/` + `tests/`）
- [x] 建立 E2E smoke 链路（参数加载→最小 ODE→产图）
- [x] 建立任务拆分方法卡与治理分配模板（多 Agent 审核闭环）
- [x] 启动下一阶段任务包：`202603021430_rna-repro-execution`
- [x] 补齐 spec P0/P1 对应实现（ODE包装+热力学+两相链路+稳定性分析）
- [x] 生成 Fig1-4 双格式图表与复现检查报告

## 快速开始

```bash
bash .harness/scripts/bootstrap_env.sh
bash .harness/scripts/run_quality_gate.sh
```

该质量门会自动执行：lint + test + build + e2e + hook replay + governance-check。

或分步执行：

```bash
.venv/bin/python scripts/e2e_smoke.py --config configs/default_params.yaml

# 生成 Fig1-4
.venv/bin/python scripts/fig1_stability.py --config configs/default_params.yaml --out figures/paper
.venv/bin/python scripts/fig2_timecourse.py --config configs/default_params.yaml --out figures/paper
.venv/bin/python scripts/fig3_spinodal.py --config configs/default_params.yaml --out figures/paper
.venv/bin/python scripts/fig4_post_segregation.py --config configs/default_params.yaml --out figures/paper

# 复现检查
.venv/bin/python scripts/check_reproduction_metrics.py --fig-dir figures/paper --out results/repro/repro_report.json --strict
```

## Harness 入口

- 工作流：`.harness/workflow.md`
- 当前任务：`.harness/.current-task`
- 核心规范：`.harness/spec/`
- Hook 配置（Codex 版）：`.codex/config.toml`
- 兼容配置（可选）：`.claude/settings.json`

## 关于规范来源

`/home/eric/harness/references/` 是上游系统管理知识库；
本项目以 `.harness/spec/` 作为落地执行层，并按里程碑进行对照同步。

## 运维与审计

```bash
bash .harness/scripts/opsctl.sh full-check
```


```bash
bash .harness/scripts/opsctl.sh governance-check --strict
```
