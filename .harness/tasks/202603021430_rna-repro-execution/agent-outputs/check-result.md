# check-result

## 验证命令执行
- [ ] lint: `.venv/bin/python -m ruff check src tests`
- [ ] test: `.venv/bin/python -m pytest -q`
- [ ] build: `.venv/bin/python -m compileall -q src`
- [ ] e2e: `bash .harness/scripts/e2e_smoke.sh`
- [ ] hook replay: `bash .harness/scripts/hook_replay.sh`
- [ ] ops full-check: `bash .harness/scripts/opsctl.sh full-check --strict`

## 失败项与修复建议
- 

## 结论
- [ ] 通过
- [ ] 未通过
