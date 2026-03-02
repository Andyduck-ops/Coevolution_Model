# RNA LLPS Coevolution Reproduction

面向论文 **A Coevolution Model of Stress-Driven RNA–Peptide Functional Enhancement and Liquid–Liquid Phase Separation** 的本地复现工程。

## 当前阶段

- [x] 搭建 `.harness/` 执行环境（hooks + quality gate + task context）
- [x] 固化工程依赖版本（`pyproject.toml`）
- [x] 建立最小可运行 Python 脚手架（`src/` + `tests/`）
- [x] 建立 E2E smoke 链路（参数加载→最小 ODE→产图）
- [ ] 补齐 spec P0 条目并进入论文模型实现

## 快速开始

```bash
bash .harness/scripts/bootstrap_env.sh
bash .harness/scripts/run_quality_gate.sh
```

该质量门会自动执行：lint + test + build + e2e + hook replay + governance-check。

或分步执行：

```bash
.venv/bin/python scripts/e2e_smoke.py --config configs/default_params.yaml
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
