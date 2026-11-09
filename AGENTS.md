# FtpServer 项目约束

## 项目结构与模块组织
`ftpServer.py` 是 Windows 图形界面入口和 FTP 服务启动文件。仓库根目录下的 `Settings.py` 负责配置读写，`UserList.py` 负责多用户 CSV 解析，`myUtils.py` 提供图标、路径等通用工具。`mypyftpdlib/` 是本项目使用的定制版 FTP 库。`ftpServer.build/`、`ftpServer.dist/`、`ftpServer.onefile-build/` 都属于生成产物，不要手工修改。`FtpServer.json`、`FtpServerUserList.csv` 这类运行期数据提交前应先脱敏。

```
ftpServer.py          # 主入口：GUI (Tkinter) + FTP 服务器生命周期
├── Settings.py       # 持久化配置 (JSON) - 端口、编码、凭据
├── UserList.py       # 多用户 CSV 解析器，用于 FtpServerUserList.csv
├── myUtils.py        # 工具函数及图标资源（base64 内嵌）
└── mypyftpdlib/      # 本地化 pyftpdlib v2.2.0（中文日志）
    ├── authorizers/  # DummyAuthorizer 用户认证
    ├── handlers/     # FTPHandler, TLS_FTPHandler
    └── servers/      # ThreadedFTPServer
```

## 构建、测试与开发命令
建议在 Windows PowerShell 中开发：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pywin32_postinstall -install
python .\ftpServer.py
```

`python .\ftpServer.py` 用于本地启动程序。

## 编码风格与命名约定
遵循当前代码风格：使用 4 空格缩进，新写或修改的逻辑尽量补充类型标注；函数和局部变量使用 `snake_case`，类名使用 `PascalCase`。保留现有模块命名方式，如 `Settings.py`、`UserList.py`。优先抽取小型辅助函数，避免继续堆积超长内联逻辑；统一复用 `logging.getLogger("ftpserver")`；无明确必要不要新增第三方依赖。

## 测试规范
当前仓库没有自带的一方自动化测试。新增逻辑时，优先在新建的 `tests/` 目录下补充 `pytest` 或 `unittest` 用例，文件命名采用 `test_*.py`。涉及界面改动时，尽量把可测试的纯逻辑从 Tkinter 代码中拆出来。最低要求是手动验证程序启动、服务启停、配置持久化，以及你修改到的 FTPS 或多用户流程。

## 提交与合并请求规范
最近提交历史以简短、祈使式中文标题为主，例如 `改进端口验证逻辑`、`修复证书文件路径检查错误`。每次提交尽量只聚焦一个行为变化，标题描述结果而不是过程。提交 PR 时应说明用户可见变化、列出手动验证步骤、注明配置或打包影响；若涉及界面改动，请附截图。除非目标就是发布制品，否则不要提交新的生成二进制文件。

## 安全与配置提示
不要提交真实用户名、密码、TLS 私钥或证书。`FtpServer.json` 和 CSV 示例中请使用占位值；如果修改默认端口、权限行为或配置格式，需要同步更新 `README.md`。
