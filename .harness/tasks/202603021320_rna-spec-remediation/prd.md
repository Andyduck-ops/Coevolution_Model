# PRD: RNA Spec 修补 + Harness 脚手架

## 目标
在进入大规模实现前，补齐数学/技术/图表的关键规范缺口，并建立端到端可验证的 harness 执行环境。

## Success Criteria
- SC-1: P0 规范条目在 spec 中落地且可追踪。
- SC-2: `.harness` hooks 可被 Claude 配置调用。
- SC-3: 本地可执行最小验证命令（lint/test/build）至少一次通过。
- SC-4: Git 远端指向 `Andyduck-ops/Coevolution_Model` 并可用于后续上传。
- SC-5: E2E smoke 链路（参数加载→最小 ODE→产图）可运行。

## Boundaries
- Always: 新增 harness 文件、工程脚手架、测试基础设施。
- Ask: 涉及覆盖现有核心论文文档时。
- Never: 执行破坏性 git/reset/清空历史操作。

## Permission Ladder
- L1: 读取/检索（只读）
- L2: 执行验证（lint/test/build）
- L3: 修改代码与脚本
- L4: 外部系统操作（push/发布）

## Structured Escalation
以下任一条件触发结构化升级：
1. 同类失败达到 2 次。
2. 关键上下文缺失（无法判定实现边界）。
3. 需要执行 L4。
4. 多方案权衡不可自动裁决。

升级输出必须包含：阻塞原因、已尝试策略、A/B 方案、风险与默认建议。

## Verification Commands
- `.venv/bin/python -m ruff check src tests`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m compileall -q src`
- `bash .harness/scripts/e2e_smoke.sh`

- `bash .harness/scripts/opsctl.sh full-check`
