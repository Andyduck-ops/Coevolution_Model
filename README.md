# RNA LLPS Coevolution Reproduction

面向论文 **A Coevolution Model of Stress-Driven RNA–Peptide Functional Enhancement and Liquid–Liquid Phase Separation** 的本地复现工程。

## 当前阶段

- [x] 搭建 `.harness/` 执行环境（hooks + quality gate + task context）
- [x] 固化工程依赖版本（`pyproject.toml`）
- [x] 建立最小可运行 Python 脚手架（`src/` + `tests/`）
- [ ] 补齐 spec P0 条目并进入模型实现

## 快速开始

```bash
bash .harness/scripts/bootstrap_env.sh
bash .harness/scripts/run_quality_gate.sh
```

## Harness 入口

- 工作流：`.harness/workflow.md`
- 当前任务：`.harness/.current-task`
- 核心规范：`.harness/spec/`
- Hook 配置：`.claude/settings.json`

## 与现有 Trellis 规范关系

当前仓库保留 `.trellis/spec/` 作为已有规范资产；`.harness/spec/` 负责执行注入与质量门。
