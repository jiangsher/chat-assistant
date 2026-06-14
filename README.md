# 聊天助手

聊天助手是一个 Windows 本地桌面悬浮窗工具。它可以自动查找当前屏幕中的聊天列表、候选人列表或工单列表，通过本地截图和 OCR 识别未读消息，并在悬浮窗中展示未读联系人、消息摘要和时间。

> 当前项目仍是 MVP 阶段，适合本地测试、演示和继续迭代。

## 普通用户：下载使用

1. 打开本项目的 GitHub `Releases` 页面。
2. 下载最新版本的 `ChatAssistant-windows.zip`。
3. 右键压缩包，选择“全部解压缩”。
4. 进入解压后的文件夹，双击 `ChatAssistant.exe` 启动。
5. 点击“自动识别”，工具会自动查找当前页面的消息列表。
6. 如果自动识别失败或识别错区域，点击“选择区域”手动框选列表区域。

注意：`ChatAssistant.exe` 必须和 `_internal` 文件夹在同一层级，不要只复制 exe 单独运行。

## 使用建议

- 自动识别适合当前屏幕上只有一个主要聊天/候选人/工单列表的场景。
- 如果页面上同时有多个列表，建议使用“选择区域”手动框选目标列表。
- 切换到新页面后，可以重新点击“自动识别”。
- 点击“刷新”时，如果已经有识别区域，会继续使用该区域，不会每 10 秒都全屏扫描。
- 工具会在截图前短暂隐藏悬浮窗，避免把自己截进识别区域。

## 开发者：从源码运行

```powershell
git clone <你的仓库地址>
cd recognize
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m recognize
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## 本地打包

安装 PyInstaller：

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
```

生成 Windows 可执行包：

```powershell
.\scripts\build.ps1
```

成功后会生成：

- `dist\ChatAssistant\ChatAssistant.exe`
- `dist\ChatAssistant-windows.zip`

## GitHub 发布

本项目包含两个 GitHub Actions workflow：

- `CI`：每次 push / pull request 自动安装依赖并运行测试。
- `Release`：推送版本 tag 时自动打包 Windows zip 并上传到 GitHub Release。

发布一个版本：

```powershell
git tag v0.2.0
git push origin v0.2.0
```

等待 GitHub Actions 完成后，`Releases` 页面会出现 `ChatAssistant-windows.zip`。

## 已实现能力

- PySide6 桌面悬浮窗。
- 自动查找当前屏幕中的消息列表区域。
- 手动框选识别区域兜底。
- 截图前自动隐藏悬浮窗，避免遮挡识别区域。
- 本地 OCR 识别。
- 未读角标检测。
- BOSS、QQ、企业微信、Gmail、LinkedIn、工单列表等模板化解析。
- 只展示未读联系人/未读消息。
- 点击悬浮窗结果卡片后跳转到原列表对应对话。
- 暂停/继续、刷新、复制、调试模式。

## 隐私说明

默认情况下，截图、OCR 和解析都在本机完成。请不要把真实聊天记录、候选人资料、手机号、邮箱、简历截图或其他敏感信息提交到 GitHub。

本仓库的 `.gitignore` 已忽略：

- `.venv/`
- `data/config.json`
- `data/debug/`
- `data/logs/`
- `dist/`
- `build/`
- Python 缓存文件

更多说明见 [docs/privacy.md](docs/privacy.md)。

## 许可

本项目使用 MIT License，见 [LICENSE](LICENSE)。
