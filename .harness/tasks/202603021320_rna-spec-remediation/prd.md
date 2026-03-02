# PRD: RNA Spec 修补 + Harness 脚手架

## 目标
在进入大规模实现前，补齐数学/技术/图表的关键规范缺口，并建立端到端可验证的 harness 执行环境。

## Success Criteria
- SC-1: P0 规范条目在 spec 中落地且可追踪。
- SC-2: `.harness` hooks 可被 Claude 配置调用。
- SC-3: 本地可执行最小验证命令（lint/test/build）至少一次通过。
- SC-4: Git 远端指向 `Andyduck-ops/Coevolution_Model` 并可用于后续上传。

## Boundaries
- Always: 新增 harness 文件、工程脚手架、测试基础设施。
- Ask: 涉及覆盖现有核心论文文档时。
- Never: 执行破坏性 git/reset/清空历史操作。

## Verification Commands
- `.venv/bin/python -m ruff check src tests`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m compileall -q src`
