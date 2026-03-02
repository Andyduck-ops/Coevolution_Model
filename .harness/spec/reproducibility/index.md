# Reproducibility & Publication Compliance

## 学术复现底线

1. 依赖版本可锁定（`pyproject.toml` + lock 文件）。
2. 一键复现命令存在（`just all` 或等价）。
3. 数据/代码可用性声明可直接写入论文补充材料。
4. 结果产物与参数配置可追溯。

## 本项目交付清单

- README：环境、运行、复现路径
- `configs/default_params.yaml`
- `scripts/`：复现实验入口
- `tests/`：核心数值与回归测试
- `figures/`：标准化导出路径

## 对齐来源（在现有 prd 中已引用）

- APS / PLOS / Nature 相关代码与可复现实践
