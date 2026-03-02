# Review Gate（多Agent审核门）

## 审核目标

确保 `check` 阶段不是“只跑命令”，而是有可追溯的审核产物与审核职责。

## 最低审核合同

1. `agent-outputs/check-result.md` 必须包含：
   - 已执行命令清单（lint/test/build/e2e/hook replay/ops）
   - 失败项与修复说明
   - 最终结论（通过/未通过）
2. 审核元数据必须存在：`evidence/review_meta.json`
   - `implementer`
   - `reviewer`
   - `review_scope`
   - `review_time_utc`
3. 审核独立性：`implementer != reviewer`
4. 若 `spec_audit_report.errors > 0`，审核必须判定未通过。
5. 角色绑定：`review_meta` 中 implementer/reviewer 必须与 `task.json.agents` 一致。

## 阻断规则

- 缺任一审核工件：阻断
- 审核独立性不满足：阻断
- 关键审计未过仍标“通过”：阻断
