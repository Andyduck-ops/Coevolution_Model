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

## 失败项与修复建议
- 无阻断失败。

## 结论
- [x] 通过
- [ ] 未通过
