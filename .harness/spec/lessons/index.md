# Lessons Index

> Lessons are runtime patches for Agent architecture deficits.

## Framework: ANCHOR / SHAPE / DECODE / ESCAPE

| Type | Patches | 适用触发 |
|---|---|---|
| [ANCHOR](./ANCHOR.md) | 反臆测补丁 | 准备引用不存在的方程/参数/文件时 |
| [SHAPE](./SHAPE.md) | 输出与上下文适配 | 文档超长、规范多层嵌套、信息爆炸时 |
| [DECODE](./DECODE.md) | 信号校验补丁 | “看起来成功”但无可复现实证时 |
| [ESCAPE](./ESCAPE.md) | 破循环补丁 | 重复失败或同一路径修不动时 |

## Top Lessons (RNA 项目)

1. **方程标题不等于可复现规范**：`equations-reference.md` 中有标题但公式为空时，必须阻断进入实现。
2. **依赖版本不钉死会直接破坏复现实验**：科学计算仓库必须给出上下界。
3. **图表函数需要“包装函数 + 参数扫描模板 + 验证口径”三件套**，缺一不可。
4. **Hook 先落地再谈自主执行**：没有质量门就没有“自动化完成”。
