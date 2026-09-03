# 先读这里：AI 项目启动包

这个文件是用户和 coding agent 的统一入口。收到本目录后，先阅读
`PROJECT_REQUEST.md`，再开始改代码或生成文档。

## 默认目标

任何项目默认只交付两样东西：

1. 可运行、可复现的项目目录（代码、数据说明、结果和 README）。
2. 一份正式但不过度包装的 PDF 报告：`paper/main.pdf`。

如果用户只要求“做代码”“生成 PDF”或“先在本地完成”，到本地交付为止，不执行外部发布。

如果用户说“上传代码”“发布项目”“放到 GitHub”或其他明确发布措辞，本机个人默认含义是一个完整闭环：

1. 创建或更新 **public GitHub 仓库**；
2. 把 PDF、项目记录和公开代码链接同步到 `3099404236.github.io`；
3. 等待 GitHub Pages 部署，并验证项目页和 PDF 直链均可公开访问。

只有用户明确说“仓库私有”或“不同步主页”时，才分别跳过公开或主页同步。`本机私用 ZIP`
只表示压缩包内含本机 DPAPI 加密密钥、压缩包本身不能上传；它不表示清理后的项目仓库应当私有。

下面这些仍然是可选项，只有需求表明确勾选或用户明确提出时才做：

- 简洁幻灯片；
- 精美汇报稿；
- GitHub Release；
- Zenodo 草稿或正式 DOI；
- 对外讨论帖。

## Agent 执行顺序

1. 阅读 `PROJECT_REQUEST.md`，识别项目类型、输入材料和本次交付范围。
2. 检查输入文件，不清楚但不影响工作的细节可先采用合理默认值。
3. 把代码放入 `code/`，数据或数据说明放入 `data/`，结果放入 `results/`。
4. 用 `paper/main.typ` 写报告并编译 `paper/main.pdf`。
5. 更新根目录 `README.md`，写清项目是什么、怎样运行、结果在哪里。
6. 填写 `publish.json`，执行本地构建和视觉检查。
7. 若用户表达上传/发布意图，执行 public GitHub + 完整主页同步；Release 和 Zenodo 仍需单独授权。

不要把普通工具项目强行包装成论文。工具、应用和探索性研究都可以只保留代码和
PDF 报告。

## 模板怎么选

详细选择规则见 `TEMPLATE_OPTIONS.md`。最简单的判断是：

| 场景 | 选择 |
| --- | --- |
| 普通项目、工具、探索性实验 | 只用 `paper/main.typ` |
| 需要快速讲解 | 加用 `slides/main.typ`（Touying/Stargazer） |
| 导师汇报、答辩、正式演讲 | 参考 `slides/polished-sample.pdf` 单独制作精美稿 |

## 本地命令

只构建报告并渲染第一页：

```powershell
.\scripts\build-local.ps1
```

同时构建简洁幻灯片：

```powershell
.\scripts\build-local.ps1 -WithSlides
```

生成新的干净交接 ZIP：

```powershell
.\scripts\create-project-kit.ps1
```

## 发布边界

- `build-local.ps1` 只在本地生成文件，不推送任何内容。
- `publish-note.ps1` 才会提交和推送 GitHub。
- 非 `-LocalOnly` 发布默认同步个人主页；只有显式传入 `-SkipHomepage` 才跳过。
- 发布默认要求 GitHub 仓库为 public；只有显式传入 `-Private` 才保留私有。
- 主页同步必须同时更新 PDF、`data/publications.json`、生成页面并验证公开链接，不能只复制 PDF。
- `zenodo-draft.ps1` 默认只创建或更新未发布草稿。
- `zenodo-draft.ps1 -Publish` 只有在用户明确说“正式发布”时才允许执行。
- API key、Personal Access Token 和 Zenodo token 不能以明文写入文件或 ZIP。

如果需要让本机 agent 自动使用密钥，请阅读 `SECRETS.md`。项目支持把密钥保存为
Windows DPAPI 加密文件，并生成仅供本机使用的私用 ZIP；公开安全包仍然不含密钥。

## 完成标准

Agent 结束任务前至少要确认：

- 主程序可以运行，或明确说明无法运行的外部依赖；
- `paper/main.pdf` 已实际编译；
- 修改过的 PDF 页面已经渲染检查；
- 没有占位符、密钥、绝对本机路径或无关缓存进入交付包；
- 若已发布，GitHub 仓库可见性与预期一致，主页项目页和 PDF 直链均返回 200；
- 最终回复列出生成文件、验证结果和未执行的可选发布动作。
