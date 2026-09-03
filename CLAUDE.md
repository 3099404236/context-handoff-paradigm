# Claude Code Instructions

先阅读 `START_HERE.md` 和 `PROJECT_REQUEST.md`，再按照 `TEMPLATE_OPTIONS.md` 选择产出。

默认先完成可复现项目目录、README 和 `paper/main.pdf`。只要求本地结果时不发布；用户
说“上传/发布”时，默认使用 public GitHub，并完整同步个人主页项目条目、PDF 和代码链接。
只有用户明确说私有或不同步主页时才例外。除非用户明确要求，否则不要制作幻灯片、
Release 或 Zenodo。

“本机私用 ZIP”不得上传，但这条警告不适用于已经排除密钥和私用 ZIP 的项目代码仓库。

如存在 `.secrets.local.json`，只能通过 `scripts/load-secrets.ps1` 加载，禁止显示密钥值。
