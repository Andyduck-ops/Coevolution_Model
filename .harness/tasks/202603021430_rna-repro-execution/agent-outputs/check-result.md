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
- [ ] claim gate 通过（当前 E1/E2/E3/E4 未通过）
- [ ] ablation gate 通过（当前 R2/R3/R4 未通过）
- [ ] integrated paper gate 通过（当前为 false）

## 失败项与修复建议
- 失败主因 1：当前“最佳实现”与论文命题方向不一致（例如 E1 应激单调律方向相反）。
- 失败主因 2：`chi_eff` 与 `chi_c` 在默认参数下同为常零，导致 E4 无法给出唯一 crossing。
- 失败主因 3：保真门禁与 claim/ablation 门禁都提示需要参数标定与模型结构细化。

## 结论
- [x] 通过
- [ ] 未通过
