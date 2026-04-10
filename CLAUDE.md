# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Windows FTP server with Tkinter GUI. Supports IPv4/IPv6, FTPS (TLS/SSL), multi-user configuration via CSV, and system tray integration.

## Commands

### Run the application
```bash
python ftpServer.py
```

### Install dependencies
```bash
pip install Pillow pypiwin32 pystray pyopenssl pyasynchat windows-curses
```

### Build executable

**PyInstaller (recommended for quick builds):**
```bash
pyinstaller.exe -F -w .\ftpServer.py -i .\ftpServer.ico --version-file .\file_version_info.txt
# Or use the spec file after first build:
pyinstaller.exe .\ftpServer.spec
```

**Nuitka (for optimized builds):**
```bash
python -m nuitka .\ftpServer.py --windows-icon-from-ico=.\ftpServer.ico --standalone --lto=yes --python-flag=-O --enable-plugin=tk-inter --windows-console-mode=disable --company-name=JARK006 --product-name=ftpServer --file-version=1.25.0.0 --product-version=1.25.0.0 --file-description="FtpServer Github@JARK006" --copyright="Copyright (C) 2023-2026 Github@JARK006"
```

### Generate SSL certificates for FTPS
```bash
openssl req -x509 -newkey rsa:2048 -keyout ftpServer.key -out ftpServer.crt -nodes -days 36500
```

## Architecture

```
ftpServer.py          # Main entry point: GUI (Tkinter) + FTP server lifecycle
├── Settings.py       # Persistent config (JSON) - ports, encoding, credentials
├── UserList.py       # Multi-user CSV parser for FtpServerUserList.csv
├── myUtils.py        # Icon resources (base64 embedded)
└── mypyftpdlib/      # Localized pyftpdlib v2.2.0 (Chinese logs)
    ├── authorizers/  # DummyAuthorizer for user authentication
    ├── handlers/     # FTPHandler, TLS_FTPHandler
    └── servers/      # ThreadedFTPServer
```

### Key Design Patterns

1. **GUI/Main Thread**: Tkinter event loop (`window.mainloop()`)
2. **FTP Server Threads**: Separate threads for IPv4/IPv6 servers (`serverThreadFun`)
3. **Log Queue**: `queue.Queue` bridges FTP server logs to GUI text widget
4. **System Tray**: `pystray.Icon` runs in daemon thread, window hides to tray on close

### Configuration Files

| File | Purpose |
|------|---------|
| `ftpServer.json` | Auto-generated settings (port, user, directory history) |
| `FtpServerUserList.csv` | Optional multi-user config (disables GUI user settings) |
| `ftpServer.crt` + `ftpServer.key` | Optional SSL certs enable FTPS |

### Permission System

User permissions are character codes passed to `DummyAuthorizer.add_user()`:
- Read: `e` (CWD), `l` (LIST), `r` (RETR)
- Write: `a` (APPE), `d` (DELETE), `f` (RENAME), `m` (MKD), `w` (STOR), `M` (CHMOD), `T` (MFMT)

Predefined: `elr` (readonly), `elradfmwMT` (readwrite)

## Notes

- Password storage uses SHA-256 with salt prefix `ENCRY`
- Supports both UTF-8 and GBK encoding for Chinese filenames
- DPI scaling handled via `ctypes.windll.shcore.SetProcessDpiAwareness(2)`
