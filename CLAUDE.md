# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供代码库工作指导。

## 项目概述

一个基于 Tkinter GUI 的 Windows FTP 服务器。支持 IPv4/IPv6、FTPS (TLS/SSL)、CSV 多用户配置及系统托盘集成。

## 命令

### 运行应用
```bash
python ftpServer.py
```

### 安装依赖
```bash
pip install Pillow pywin32 pystray pyopenssl pyasynchat windows-curses
# 或者直接安装 requirements.txt
pip install -r requirements.txt
# pywin32 还需后安装
pywin32_postinstall -install
```

### 构建可执行文件

**PyInstaller（推荐用于快速构建）：**
```bash
pyinstaller.exe -F -w .\ftpServer.py -i .\ftpServer.ico --version-file .\file_version_info.txt
# 首次构建后可使用 spec 文件：
pyinstaller.exe .\ftpServer.spec
```

**Nuitka（用于优化构建）：**
```bash
python -m nuitka .\ftpServer.py --windows-icon-from-ico=.\ftpServer.ico --standalone --lto=yes --python-flag=-O --enable-plugin=tk-inter --windows-console-mode=disable --company-name=JARK006 --product-name=ftpServer --file-version=1.26.0.0 --product-version=1.26.0.0 --file-description="FtpServer Github@JARK006" --copyright="Copyright (C) 2023-2026 Github@JARK006"
```

## 架构

```
ftpServer.py          # 主入口：GUI (Tkinter) + FTP 服务器生命周期
├── Settings.py       # 持久化配置 (JSON) - 端口、编码、凭据
├── UserList.py       # 多用户 CSV 解析器，用于 FtpServerUserList.csv
├── myUtils.py        # 图标资源（base64 内嵌）
└── mypyftpdlib/      # 本地化 pyftpdlib v2.2.0（中文日志）
    ├── authorizers/  # DummyAuthorizer 用户认证
    ├── handlers/     # FTPHandler, TLS_FTPHandler
    └── servers/      # ThreadedFTPServer
```

### 关键设计模式

1. **GUI/主线程**：Tkinter 事件循环 (`window.mainloop()`)
2. **FTP 服务器线程**：IPv4/IPv6 服务器的独立线程 (`serverThreadFun`)
3. **日志队列**：`queue.Queue` 将 FTP 服务器日志桥接到 GUI 文本控件
4. **系统托盘**：`pystray.Icon` 在守护线程中运行，关闭窗口时最小化到托盘

### 配置文件

| 文件 | 用途 |
|------|------|
| `ftpServer.json` | 自动生成的设置（端口、用户、目录历史） |
| `FtpServerUserList.csv` | 可选的多用户配置（启用后禁用 GUI 用户设置） |
| `ftpServer.crt` + `ftpServer.key` | 可选 TLS/SSL 证书，启用 FTPS |

### 权限系统

用户权限为传递给 `DummyAuthorizer.add_user()` 的字符代码：
- 读取：`e` (CWD), `l` (LIST), `r` (RETR)
- 写入：`a` (APPE), `d` (DELETE), `f` (RENAME), `m` (MKD), `w` (STOR), `M` (CHMOD), `T` (MFMT)

预定义：`elr`（只读），`elradfmwMT`（读写）

## 备注

- 密码存储使用 SHA-256，带盐值前缀 `ENCRY`
- 同时支持 UTF-8 和 GBK 编码以处理中文文件名
- DPI 缩放通过 `ctypes.windll.shcore.SetProcessDpiAwareness(2)` 处理
