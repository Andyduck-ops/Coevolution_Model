# check-result

## 验证命令执行
- [x] lint: `.venv/bin/python -m ruff check src tests`
- [x] test: `.venv/bin/python -m pytest -q`
- [x] build: `.venv/bin/python -m compileall -q src`
- [x] e2e: `bash .harness/scripts/e2e_smoke.sh`
- [x] hook replay: `bash .harness/scripts/hook_replay.sh`
- [x] ops full-check: `bash .harness/scripts/opsctl.sh full-check --strict`

## 复现产物验证
- [x] `figures/paper/fig1_stability.(png|pdf)`
- [x] `figures/paper/fig2_timecourse.(png|pdf)`
- [x] `figures/paper/fig3_spinodal.(png|pdf)`
- [x] `figures/paper/fig4_post_segregation.(png|pdf)`
- [x] `results/repro/repro_report.json`（`passed=true`）

## 保真校验（新增）
- [x] 已支持 `--require-fidelity` 图像保真门禁（参考图自动探测/显式指定）
- [ ] 当前阈值 `composite>=0.75` 未通过（四图约 `0.686~0.713`）
- [ ] 需要下一轮进行参数标定/曲线拟合后再复核

## 论文命题与消融检查（并行端到端）
- [x] 生成 `results/repro/claim_report.json`
- [x] 生成 `results/repro/ablation_report.json`
- [x] 生成 `results/repro/paper_validation_report.json`
- [x] claim gate 通过（当前 E1-E5 全通过）
- [ ] ablation gate 通过（当前 R1/R2/R4 通过，R3 未通过）
- [ ] integrated paper gate 通过（当前为 false）

## 失败项与修复建议
- 已修复：E1 单调方向、E4 crossing 计数、热力学阈值定义与核心 ODE 结构对齐后，claim gate 已转绿。
- 当前主失败：ablation gate（仅 R3 失败）与 repro fidelity gate（四图 composite<0.75）。
- 后续建议：聚焦 R3 的 post-seg 机制一致性修复与 Fig1-4 曲线级标定。

## 结论
- [x] 通过
- [ ] 未通过
