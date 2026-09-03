# Agent Instructions

开始工作前必须依次阅读：

1. `START_HERE.md`
2. `PROJECT_REQUEST.md`
3. `TEMPLATE_OPTIONS.md`
4. `AGENT_BRIEF.md`（需要详细发布规则时）

默认先完成项目代码、README 和 `paper/main.pdf`。如果用户只要求本地结果，不执行外部发布；
如果用户说“上传/发布”，默认创建或更新 public GitHub 仓库，并把 PDF、主页项目记录和
公开代码链接完整同步到 `3099404236.github.io`。只有明确要求私有或不同步时才例外。
幻灯片、Release、Zenodo 和讨论帖仍需单独授权。不得把 token 或 API key 写入文件。

“本机私用 ZIP”只表示该 ZIP 含 DPAPI 加密密钥且不得上传，不代表清理后的项目代码仓库
必须私有。发布前应检查 `.secrets.local.json`、私用 ZIP 和密钥未进入 Git。

如果根目录存在 `.secrets.local.json`，按 `SECRETS.md` 使用
`scripts/load-secrets.ps1` 加载。不得打印、记录或提交解密后的值。
