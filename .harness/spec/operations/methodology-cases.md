# Methodology Cases（来自 references 的落地映射）

> 目的：不是“引用参考文献”，而是把案例方法论变成可运行系统。

## Case A: hook-based-enforcement

来源：`references/.../quality-enforcement/hook-based-enforcement.md`

落地：
- `session_start` 注入全局上下文；
- `pre_tool_use` 做阶段上下文注入；
- `post_tool_use` 做 staleness 检测；
- `subagent_stop` 执行质量门。

实现文件：`.codex/config.toml` + `.harness/hooks/*.py`

## Case B: failure-budget + structured-escalation

来源：
- `agent-lifecycle/failure-budget.md`
- `agent-lifecycle/structured-escalation.md`

落地：
- debug 同类失败预算 = 3；
- 超预算返回阻断决策并要求 A/B 方案升级。

实现文件：`.harness/hooks/quality-gate.py`、`.harness/spec/operations/permission-ladder.md`

## Case C: progressive-disclosure

来源：`context-injection/progressive-disclosure.md`

落地：
- 采用 JSONL 声明式注入（implement/check/debug）；
- 自动从 PRD 提取相关文件路径，减少无关上下文。

实现文件：`.harness/hooks/inject-context.py` + `tasks/*/*.jsonl`

## Case D: staleness-detection

来源：`knowledge-evolution/staleness-detection.md`

落地：
- Edit/Write 后检测 spec 与代码漂移；
- 漂移结果写入 `.harness/.stale-knowledge.json`；
- session start 注入漂移告警。

实现文件：`.harness/hooks/track-staleness.py` + `.harness/hooks/session-start.py`

## Case E: contract-replay-verification-gate（轻量版）

来源：`fullstack-engineering/contract-replay-verification-gate.md`

落地：
- 在 check 阶段强制 “lint + test + build + e2e + hook replay + ops full-check”；
- 审计报告落盘并回写任务 evidence。

实现文件：
- `.harness/scripts/run_quality_gate.sh`
- `.harness/scripts/hook_replay.py`
- `.harness/scripts/ops_manager.py`
