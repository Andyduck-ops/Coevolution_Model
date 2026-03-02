# 技术栈规范

## 语言与版本

- **Python >= 3.10,<3.13**
- 使用 type hints 提高可读性与可维护性

## 依赖管理

- **工具**: `uv` (依赖安装) + `pyproject.toml` (PEP 621)
- **Lock 文件**: `uv.lock` 保证精确复现
- 安装方式: `uv sync` 或 `pip install -e .[dev]`

## 核心依赖（必须钉版本）

| 包名 | 版本约束 | 用途 |
|------|----------|------|
| `numpy` | `numpy>=1.24,<2.0` | 数值数组与线性代数 |
| `scipy` | `scipy>=1.11,<1.14` | ODE、求根、优化 |
| `matplotlib` | `matplotlib>=3.8,<3.11` | 图表复现 |
| `pyyaml` | `pyyaml>=6.0,<7.0` | 参数配置读取 |
| `tqdm` | `tqdm>=4.66,<5.0` | 参数扫描进度与批量任务可观测 |

## 开发工具

| 工具 | 用途 | 配置 |
|------|------|------|
| `ruff` | Linter + Formatter | `pyproject.toml [tool.ruff]` |
| `pytest` | 测试框架 | `pyproject.toml [tool.pytest]` |
| `pytest-cov` | 覆盖率 | `pyproject.toml [project.optional-dependencies.dev]` |
| `uv` | 依赖管理 | `pyproject.toml + uv.lock` |

## Ruff 配置

- 规则集合：`E,F,I,B,UP`
- 行宽：`100`
- target-version：`py310`

## 开源许可

- **MIT License**
- 学术计算标准选择，与 SciPy/NumPy 社区生态一致
- 满足 APS/PLOS/Nature 期刊代码共享要求

## Git 规范

- `.gitignore` 排除: `__pycache__/`, `.venv/`, `*.egg-info/`, `figures/`, `results/`
- 提交格式: `type(scope): description`
  - type: feat / fix / docs / refactor / test / chore
  - scope: models / thermo / analysis / viz / config / harness
- 版本标签: 论文提交时打 `v1.0.0`
