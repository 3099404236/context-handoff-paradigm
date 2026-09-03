# API 密钥保存方式

本项目区分两种 ZIP：

1. `AI项目启动包.zip`：公开安全包，不含任何密钥，可以上传 GitHub 或交给远程 agent。
2. 本机私用包：额外包含 `.secrets.local.json`，其中的密钥使用 Windows DPAPI 加密。

DPAPI 加密文件只能由创建它的 Windows 用户在同一台机器上解密。即使私用 ZIP 被复制到
别的机器，密钥也不能直接读取。

## 第一次保存

不要把密钥作为命令行参数，也不要再次粘贴到聊天中。运行：

```powershell
.\scripts\save-secrets.ps1
```

脚本会在终端中安全询问：

- `OPENROUTER_API_KEY`
- `ZENODO_TOKEN`

输入时内容不会显示。加密结果写入根目录 `.secrets.local.json`，该文件已被 Git 和公开
打包流程排除。

如果变量已经存在于当前或用户环境，可以运行：

```powershell
.\scripts\save-secrets.ps1 -FromEnvironment
```

## Agent 加载

在需要调用 API 的同一个 PowerShell 进程中运行：

```powershell
.\scripts\load-secrets.ps1
```

脚本只报告变量是否加载成功，不打印变量值。

## 生成本机私用包

```powershell
.\scripts\create-private-project-kit.ps1 `
  -OutputPath "..\AI项目启动包-本机私用.zip"
```

这个私用包只适合继续交给本机 agent。不要上传 GitHub、网盘公开链接、邮件附件或远程
聊天服务。

**重要：私用 ZIP 不得上传，不等于项目仓库必须设为 private。** 清理并确认
`.secrets.local.json`、私用 ZIP、token 和 API key 都没有进入 Git 后，项目代码按个人
默认应发布到 public GitHub；存在 PDF 时还应同步个人主页。私用和公开描述的是压缩包中
是否包含本机密钥，不是项目仓库的可见性。

## 轮换规则

任何曾经粘贴进聊天、截图或公开文件的密钥都应当在服务商后台撤销并重新生成。重新生成后，
再次运行 `save-secrets.ps1` 覆盖本地加密文件即可。
