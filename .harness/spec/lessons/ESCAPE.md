# ESCAPE — Loop Breaking Patches

> When you've tried the same approach twice and it still fails, CHANGE DIRECTION.

These lessons fix the **local optima deficit**: Agent repeats the same failing
strategy with minor variations instead of fundamentally changing approach.

## Lessons

<!-- Add lessons from /harness:compound -->

_No lessons yet._

## Common ESCAPE Patterns

- 2 consecutive same-type failures → change strategy entirely
- If fixing one test breaks another → step back, rethink architecture
- If a dependency won't install → try alternative package or approach
- If regex keeps failing → switch to AST-based approach
- 3 total failures → escalate to human (failure budget exhausted)

## RNA 项目补丁（来自 codex skills 的适配）

- 连续 2 次同类失败，禁止“微调重试”；必须切换策略（例如：数值法→解析近似验证）。
- 第 3 次失败触发人工升级，输出 A/B/C 方案及权衡。
- 结束任务前必须满足“完成承诺”：
  - 已有代码变更
  - 已运行验证命令
  - 已记录风险与下一步
