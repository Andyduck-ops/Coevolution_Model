# DECODE — Signal Verification Patches

> When a tool says "success" or says nothing, verify independently.

These lessons fix the **perception blindness deficit**: Agent trusts tool output
at face value without verifying the actual effect.

## Lessons

<!-- Add lessons from /harness:compound -->

_No lessons yet._

## Common DECODE Patterns

- sed with no output doesn't mean success (verify the file changed)
- Empty test output might mean tests didn't run (check exit code)
- "Build succeeded" doesn't mean the feature works (run integration test)
- Git push "success" — check remote actually received the commits

## RNA 项目补丁（来自 codex skills 的适配）

- “函数已定义”不等于“图可复现”：必须有最小可运行入口。
- “CI 绿了”不等于“论文可复现”：必须带参数配置与图表产物路径。
- 对 review 反馈优先处理语义正确性，再考虑性能优化。
