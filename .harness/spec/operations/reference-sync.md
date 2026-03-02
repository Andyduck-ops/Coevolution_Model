# Harness References Sync Policy

## 定位

`/home/eric/harness/references/` 是上游规范知识库（system-management + patterns + lanes）。
本项目将其视为方法论来源（Method Source），并在 `.harness/spec/` 形成项目适配后的执行规范。

## 同步原则

1. 上游 `references` 提供通用方法与约束。
2. 本仓库 `.harness/spec` 只保留与 RNA 论文复现直接相关的可执行规范。
3. 若出现冲突：
   - 方法论层面遵循上游 references；
   - 工程实现层面以本仓库可执行性为准并记录差异。

## 最低同步频率

- 每个里程碑（P0/P1/P2）结束后，至少执行一次“references 对照审计”。
