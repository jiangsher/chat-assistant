# 聊天助手

聊天助手是一个 Windows 本地桌面悬浮窗工具。它可以让你框选其他软件中的聊天列表、候选人列表或工单列表，通过本地截图和 OCR 识别未读消息，并在悬浮窗中展示未读联系人、消息摘要和时间。

> 当前项目仍是 MVP 阶段，适合本地测试、演示和继续迭代。

## 普通用户：下载使用

1. 打开本项目的 GitHub `Releases` 页面。
2. 下载 `ChatAssistant-windows.zip`。
3. 解压压缩包。
4. 双击 `ChatAssistant.exe` 启动。
5. 第一次使用时，点击悬浮窗里的“选择区域”，框选当前页面需要识别的聊天/候选人/工单列表。

使用时建议只框选列表区域，不要把左侧导航、聊天详情区或悬浮窗本身框进去。切换到新页面后，请重新选择区域。

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
git tag v0.1.0
git push origin v0.1.0
```

等待 GitHub Actions 完成后，`Releases` 页面会出现 `ChatAssistant-windows.zip`。

## 已实现能力

- PySide6 桌面悬浮窗。
- 框选屏幕识别区域。
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
- `dist/`
- `build/`
- Python 缓存文件

更多说明见 [docs/privacy.md](docs/privacy.md)。

## 许可

本项目使用 MIT License，见 [LICENSE](LICENSE)。
