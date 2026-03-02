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

## 失败项与修复建议
- 无阻断失败。

## 结论
- [x] 通过
- [ ] 未通过
