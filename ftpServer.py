r"""
FTP Server with GUI Interface
一个带图形界面的FTP服务器

Author: JARK006
Email: jark006@qq.com
Github: https://github.com/jark006
Project: https://github.com/jark006/FtpServer
License: MIT License
Copyright (c) 2023-2026 JARK006

# 打包工具
    pip install Nuitka[onefile]

# 第三方库需求
    pip install -r requirements.txt

# pywin32 还需后安装
    pywin32_postinstall -install

# nuitka打包脚本 依赖解析本文件的版本变量声明 appVersion = "vX.Y"  依次打包输出 单文件及单目录
    build-nuitka.ps1
"""

# 标准库导入
import logging
import os
import queue
import socket
import sys
import threading
import time
import ctypes
import functools
import webbrowser

# GUI相关导入
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, font

# 第三方库导入
import pystray
import win32clipboard
import win32con
import win32com.client
from OpenSSL import crypto

# 本地模块导入
import Settings
import UserList
import myUtils

# 汉化 pyftpdlib 模块导入
from mypyftpdlib.authorizers import DummyAuthorizer
from mypyftpdlib.handlers import FTPHandler, TLS_FTPHandler
from mypyftpdlib.servers import ThreadedFTPServer

appLabel = "FTP文件服务器"
appVersion = "v1.27"
appAuthor = "JARK006"
githubLink = "https://github.com/jark006/FtpServer"
releaseLink = "https://github.com/jark006/FtpServer/releases"
lanzouLink = "https://jark006.lanzout.com/b0koxtm7g"
baiduLink = "https://pan.baidu.com/s/1955qjdrnPtxhNhtksjqvfg?pwd=6666"
windowsTitle = f"{appLabel} {appVersion}"

logMsg = queue.Queue()
isLogThreadRunning: bool = True
logMsgBackup: list[str] = []

permReadOnly: str = UserList.PERM_READ_ONLY
permReadWrite: str = UserList.PERM_READ_WRITE

isIPv4Supported: bool = False
isIPv6Supported: bool = False
isIPv4ThreadRunning = threading.Event()
isIPv6ThreadRunning = threading.Event()

appDirectory: str = myUtils.getAppDirectory()
certFilePath: str = os.path.join(appDirectory, "ftpServer.crt")
keyFilePath: str = os.path.join(appDirectory, "ftpServer.key")

scaleFactor: int = 100
mutex_handle: int = 0


def scale(n: int) -> int:
    global scaleFactor
    return int(n * scaleFactor / 100)


def showHelpWindow():
    global mainWindow
    global iconImage

    helpWindows = tk.Toplevel(mainWindow)
    helpWindows.geometry(f"{scale(600)}x{scale(500)}")
    helpWindows.minsize(scale(600), scale(500))
    helpWindows.title("帮助")
    helpWindows.iconphoto(False, iconImage)  # type: ignore

    uiFont = font.Font(
        family="Consolas", size=font.nametofont("TkTextFont").cget("size")
    )
    helpTextWidget = scrolledtext.ScrolledText(
        helpWindows, bg="#dddddd", wrap=tk.CHAR, font=uiFont, width=0, height=0
    )
    helpTextWidget.insert(tk.INSERT, myUtils.helpTips)
    helpTextWidget.configure(state=tk.DISABLED)
    helpTextWidget.pack(fill=tk.BOTH, expand=True)

    menu = tk.Menu(mainWindow, tearoff=False)
    menu.add_command(
        label="复制",
        command=lambda event=None: helpTextWidget.event_generate("<<Copy>>"),
    )
    helpTextWidget.bind(
        "<Button-3>", lambda event: menu.post(event.x_root, event.y_root)
    )


def showAboutWindow():
    global mainWindow
    global iconImage

    aboutWindows = tk.Toplevel(mainWindow)
    aboutWindows.resizable(False, False)
    aboutWindows.minsize(scale(400), scale(200))
    aboutWindows.title("关于")
    aboutWindows.iconphoto(False, iconImage)  # type: ignore

    headerFrame = ttk.Frame(aboutWindows)
    headerFrame.pack(fill=tk.X)
    headerFrame.grid_columnconfigure(1, weight=1)

    tk.Label(headerFrame, image=iconImage, width=scale(100), height=scale(100)).grid(
        row=0, column=0, rowspan=2
    )
    tk.Label(
        headerFrame,
        text=f"{appLabel} {appVersion}",
        font=font.Font(font=("Consolas", scale(12))),
    ).grid(row=0, column=1, sticky=tk.S)

    tk.Label(headerFrame, text=f"开发者: {appAuthor}").grid(row=1, column=1)

    linksFrame = ttk.Frame(aboutWindows)
    linksFrame.pack(fill=tk.X, padx=scale(20), pady=(0, scale(20)))

    tk.Label(linksFrame, text="Github").grid(row=0, column=0)
    tk.Label(linksFrame, text="Release").grid(row=1, column=0)
    tk.Label(linksFrame, text="蓝奏云").grid(row=2, column=0)
    tk.Label(linksFrame, text="百度云").grid(row=3, column=0)

    label1 = ttk.Label(linksFrame, text=githubLink, foreground="blue")
    label1.bind("<Button-1>", lambda event: webbrowser.open(githubLink))
    label1.grid(row=0, column=1, sticky=tk.W)

    label2 = ttk.Label(linksFrame, text=releaseLink, foreground="blue")
    label2.bind("<Button-1>", lambda event: webbrowser.open(releaseLink))
    label2.grid(row=1, column=1, sticky=tk.W)

    label3 = ttk.Label(linksFrame, text="点击跳转 提取码: 6666", foreground="blue")
    label3.bind("<Button-1>", lambda event: webbrowser.open(lanzouLink))
    label3.grid(row=2, column=1, sticky=tk.W)

    label4 = ttk.Label(linksFrame, text="点击跳转 提取码: 6666", foreground="blue")
    label4.bind("<Button-1>", lambda event: webbrowser.open(baiduLink))
    label4.grid(row=3, column=1, sticky=tk.W)


def deleteCurrentComboboxItem():
    global settings
    global directoryCombobox

    currentDirectoryList = list(directoryCombobox["value"])

    if len(currentDirectoryList) <= 1:
        settings.directoryList = [settings.appDirectory]
        directoryCombobox["value"] = tuple(settings.directoryList)
        directoryCombobox.current(0)
        logger.info("目录列表已清空, 默认恢复到程序所在目录")
        return

    currentValue = directoryCombobox.get()

    if currentValue in currentDirectoryList:
        currentIdx = directoryCombobox.current()
        currentDirectoryList.remove(currentValue)
        settings.directoryList = currentDirectoryList
        directoryCombobox["value"] = tuple(currentDirectoryList)
        if currentIdx >= len(currentDirectoryList):
            directoryCombobox.current(len(currentDirectoryList) - 1)
        else:
            directoryCombobox.current(currentIdx)
    else:
        directoryCombobox.current(0)


def onPasswordChanged():
    global isPasswordModified
    isPasswordModified = True


def updateSettingVars():
    global settings
    global directoryCombobox
    global userNameVar
    global userPasswordVar
    global IPv4PortVar
    global IPv6PortVar
    global isReadOnlyVar
    global isGBKVar
    global isAutoStartServerVar
    global isIPv4Supported
    global isIPv6Supported
    global isPasswordModified

    settings.directoryList = list(directoryCombobox["value"])
    if len(settings.directoryList) > 0:
        directory = directoryCombobox.get()
        if directory in settings.directoryList:
            settings.directoryList.remove(directory)
        settings.directoryList.insert(0, directory)
    else:
        settings.directoryList = [settings.appDirectory]

    directoryCombobox["value"] = tuple(settings.directoryList)
    directoryCombobox.current(0)

    settings.userName = userNameVar.get()
    settings.isGBK = isGBKVar.get()
    settings.isReadOnly = isReadOnlyVar.get()
    settings.isAutoStartServer = isAutoStartServerVar.get()

    passwordTmp = userPasswordVar.get()
    if isPasswordModified:
        if len(passwordTmp) == 0:
            settings.userPassword = ""
        else:
            settings.userPassword = Settings.Settings.encry2sha256(passwordTmp)
            userPasswordVar.set("******")
        isPasswordModified = False

    portStr = IPv4PortVar.get().strip()
    if len(portStr) == 0:
        settings.IPv4Port = 0
    else:
        try:
            IPv4PortInt = int(portStr)
            if 1 <= IPv4PortInt and IPv4PortInt < 65536:
                settings.IPv4Port = IPv4PortInt
            else:
                raise ValueError("IPv4 端口值异常")
        except ValueError as e:
            tips: str = (
                f"当前端口值: [ {portStr} ], 正常范围: 1 ~ 65535, 已重设为: 21"
            )
            settings.IPv4Port = 21
            IPv4PortVar.set("21")
            logger.warning(tips)
            messagebox.showwarning(str(e), tips)

    portStr = IPv6PortVar.get().strip()
    if len(portStr) == 0:
        settings.IPv6Port = 0
    else:
        try:
            IPv6PortInt = int(portStr)
            if 1 <= IPv6PortInt and IPv6PortInt < 65536:
                settings.IPv6Port = IPv6PortInt
            else:
                raise ValueError("IPv6 端口值异常")
        except ValueError as e:
            tips: str = (
                f"当前端口值: [ {portStr} ], 正常范围: 1 ~ 65535, 已重设为: 21"
            )
            settings.IPv6Port = 21
            IPv6PortVar.set("21")
            logger.warning(tips)
            messagebox.showwarning(str(e), tips)


class StdoutRedirector:  # 重定向输出
    def __init__(self):
        sys.stdout = self
        sys.stderr = self

    def write(self, info):
        logMsg.put(info)

    def flush(self):
        pass


def copyToClipboard(text: str):
    if not text or len(text.strip()) == 0:
        return

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text.strip())
    finally:
        win32clipboard.CloseClipboard()


def ip_into_int(ip_str: str) -> int:
    return functools.reduce(lambda x, y: (x << 8) + y, map(int, ip_str.split(".")))


# https://blog.mimvp.com/article/32438.html
def is_internal_ip(ip_str: str) -> bool:
    if ip_str.startswith("169.254."):
        return True

    ip_int = ip_into_int(ip_str)
    net_A = 10  # ip_into_int("10.255.255.255") >> 24
    net_B = 2753  # ip_into_int("172.31.255.255") >> 20
    net_C = 49320  # ip_into_int("192.168.255.255") >> 16
    net_ISP = 43518  # ip_into_int("100.127.255.255") >> 22
    net_DHCP = 401  # ip_into_int("169.254.255.255") >> 16
    return (
        ip_int >> 24 == net_A
        or ip_int >> 20 == net_B
        or ip_int >> 16 == net_C
        or ip_int >> 22 == net_ISP
        or ip_int >> 16 == net_DHCP
    )


def startServer():
    global settings
    global userList
    global serverThreadV4
    global serverThreadV6
    global isIPv4Supported
    global isIPv6Supported
    global isIPv4ThreadRunning
    global isIPv6ThreadRunning
    global tipsTextWidget
    global tipsTextWidgetRightClickMenu

    if isIPv4ThreadRunning.is_set():
        logger.info("IPv4 服务正在运行")
        return
    if isIPv6ThreadRunning.is_set():
        logger.info("IPv6 服务正在运行")
        return

    updateSettingVars()

    if not os.path.exists(settings.directoryList[0]):
        tips: str = (
            f"路径: [ {settings.directoryList[0]} ]异常！请检查路径是否正确或者有没有读取权限。"
        )
        logger.warning(tips)
        messagebox.showerror("路径异常", tips)
        return

    userList.load()
    if userList.isEmpty():
        if len(settings.userName) > 0 and len(settings.userPassword) == 0:
            tips: str = "!!! 请设置密码再启动服务 !!!"
            logger.warning(tips)
            messagebox.showerror("密码异常", tips)
            return
        if (
            settings.userName == "anonymous" or len(settings.userName) == 0
        ) and settings.isReadOnly == False:
            logger.warning("警告：当前允许【匿名用户】登录，且拥有【写入、修改】文件权限，请谨慎对待。")
            logger.warning("若是安全的内网环境可忽略以上警告，否则【匿名用户】应当选择【只读】权限。")

    tipsStr, ftpUrlList, isIPv4Supported, isIPv6Supported = getTipsAndUrlList()

    if len(ftpUrlList) == 0:
        tips: str = "!!! 本机没有检测到网络IP, 请检查端口设置或网络连接, 或稍后重试 !!!"
        logger.warning(tips)
        messagebox.showerror("网络或端口设置异常", tips)
        return

    settings.save()

    tipsTextWidget.configure(state=tk.NORMAL)
    tipsTextWidget.delete("1.0", tk.END)
    tipsTextWidget.insert(tk.INSERT, tipsStr)
    tipsTextWidget.configure(state=tk.DISABLED)

    tipsTextWidgetRightClickMenu.delete(0, tk.END)
    for url in ftpUrlList:
        tipsTextWidgetRightClickMenu.add_command(
            label=f"复制 {url}", command=lambda url=url: copyToClipboard(url)
        )

    try:
        authorizer = DummyAuthorizer()
        if userList.isEmpty():
            if len(settings.userName) > 0:
                authorizer.add_user(
                    settings.userName,
                    settings.userPassword,
                    settings.directoryList[0],
                    perm=permReadOnly if settings.isReadOnly else permReadWrite,
                )
            else:
                authorizer.add_anonymous(
                    settings.directoryList[0],
                    perm=permReadOnly if settings.isReadOnly else permReadWrite,
                )
        else:
            for userItem in userList.userList:
                authorizer.add_user(
                    userItem.userName,
                    userItem.password,
                    userItem.path,
                    perm=userItem.perm,
                )

        has_tls_cert = os.path.exists(certFilePath) and os.path.exists(keyFilePath)
        if has_tls_cert:
            logger.info(
                "已加载 TLS/SSL 证书文件, 默认启用 FTPS [TLS/SSL显式加密]"
            )

        hasStartServer: bool = False
        if isIPv4Supported and settings.IPv4Port > 0:
            handler = create_server_handler(authorizer, has_tls_cert, "IPv4")
            serverThreadV4 = threading.Thread(
                target=serverThreadFun, args=("IPv4", handler)
            )
            serverThreadV4.start()
            hasStartServer = True

        if isIPv6Supported and settings.IPv6Port > 0:
            handler = create_server_handler(authorizer, has_tls_cert, "IPv6")
            serverThreadV6 = threading.Thread(
                target=serverThreadFun, args=("IPv6", handler)
            )
            serverThreadV6.start()
            hasStartServer = True

        if not hasStartServer:
            tips: str = "!!! 未检测到有效端口, 服务无法启动, 请检查端口设置是否正确 !!!"
            logger.warning(tips)
            messagebox.showerror("端口异常", tips)
            return

    except Exception as e:
        tips: str = f"!!! 发生异常, 无法启动线程 !!!\n{e}"
        logger.warning(tips)
        messagebox.showerror("启动异常", tips)
        return

    if userList.isEmpty():
        logger.info(
            "\n\n用户: {}\n密码: {}\n权限: {}\n编码: {}\n目录: {}\n".format(
                (
                    settings.userName
                    if len(settings.userName) > 0
                    else "匿名访问(anonymous)"
                ),
                ("******" if len(settings.userPassword) > 0 else "无"),
                ("只读" if settings.isReadOnly else "读写"),
                ("GBK" if settings.isGBK else "UTF-8"),
                settings.directoryList[0],
            )
        )
    else:
        userList.printUserList()
        logger.info(f"编码: {'GBK' if settings.isGBK else 'UTF-8'}\n")

    setConfigWidgetsState(tk.DISABLED)


def create_server_handler(
    authorizer: DummyAuthorizer, has_tls_cert: bool, IP_Family: str
) -> type[FTPHandler]:
    base_handler = TLS_FTPHandler if has_tls_cert else FTPHandler
    handler_attrs = {
        "authorizer": authorizer,
        "encoding": "gbk" if settings.isGBK else "utf8",
        "permit_foreign_addresses": True, # 允许所有IP地址连接以适应复杂的网络环境，但有被滥用于 FTP bounce、端口探测或内网探测的风险
        "permit_privileged_ports": True,
    }

    if has_tls_cert:
        handler_attrs.update(
            {
                "certfile": certFilePath,
                "keyfile": keyFilePath,
                "tls_control_required": True,
                "tls_data_required": True,
                "ssl_context": None, # Keep TLS context cache isolated on this dynamic handler class.
            }
        )

    return type(f"{IP_Family}{base_handler.__name__}", (base_handler,), handler_attrs)


def serverThreadFun(IP_Family: str, handler: type[FTPHandler]):
    global settings
    global serverV4
    global isIPv4ThreadRunning
    global serverV6
    global isIPv6ThreadRunning

    if IP_Family == "IPv4":
        try:
            serverV4 = ThreadedFTPServer(("0.0.0.0", settings.IPv4Port), handler)
            logger.info("IPv4服务开始运行")
            isIPv4ThreadRunning.set()
            serverV4.serve_forever()
        except Exception as e:
            logger.error(f"IPv4服务异常: {e}")
        finally:
            isIPv4ThreadRunning.clear()
            logger.info("IPv4服务已停止")
    else:
        try:
            serverV6 = ThreadedFTPServer(("::", settings.IPv6Port), handler)
            logger.info("IPv6服务开始运行")
            isIPv6ThreadRunning.set()
            serverV6.serve_forever()
        except Exception as e:
            logger.error(f"IPv6服务异常: {e}")
        finally:
            isIPv6ThreadRunning.clear()
            logger.info("IPv6服务已停止")


def stopServer():
    global settings
    global serverV4
    global serverV6
    global serverThreadV4
    global serverThreadV6
    global isIPv4ThreadRunning
    global isIPv6ThreadRunning
    global isIPv4Supported
    global isIPv6Supported

    if isIPv4Supported and settings.IPv4Port > 0:
        if isIPv4ThreadRunning.is_set():
            logger.info("IPv4服务线程正在停止...")
            serverV4.close_all()
            serverThreadV4.join()
        logger.info("IPv4服务线程已停止")

    if isIPv6Supported and settings.IPv6Port > 0:
        if isIPv6ThreadRunning.is_set():
            logger.info("IPv6服务线程正在停止...")
            serverV6.close_all()
            serverThreadV6.join()
        logger.info("IPv6服务线程已停止")

    setConfigWidgetsState(tk.NORMAL)


def setConfigWidgetsState(state: str):
    for w in (
        userNameEntry, userPasswordEntry,
        IPv4PortEntry, IPv6PortEntry,
        encodingUtf8Radio, encodingGbkRadio,
        permReadWriteRadio, permReadOnlyRadio,
        directoryCombobox, pickDirButton, deleteDirButton,
    ):
        w.configure(state=state)


def pickDirectory():
    global directoryCombobox
    global settings

    directory = filedialog.askdirectory()
    if len(directory) == 0:
        return

    if os.path.exists(directory):
        if directory in settings.directoryList:
            settings.directoryList.remove(directory)
            settings.directoryList.insert(0, directory)
        else:
            settings.directoryList.insert(0, directory)

        directoryCombobox["value"] = tuple(settings.directoryList)
        directoryCombobox.current(0)
    else:
        tips: str = f"路径不存在或无访问权限: [ {directory} ]"
        logger.warning(tips)
        messagebox.showerror("路径异常", tips)


def showWindow():
    global mainWindow
    mainWindow.deiconify()


def hideWindow():
    global mainWindow
    mainWindow.withdraw()


def handleExit(strayIcon):
    global settings
    global mainWindow
    global isLogThreadRunning
    global logThread
    global mutex_handle

    # 释放互斥锁
    if mutex_handle != 0:
        kernel32 = ctypes.windll.kernel32
        kernel32.CloseHandle(mutex_handle)
        mutex_handle = 0

    updateSettingVars()
    settings.save()

    stopServer()
    strayIcon.visible = False
    strayIcon.stop()

    logger.info("等待日志线程退出...")
    isLogThreadRunning = False
    logThread.join()

    mainWindow.destroy()
    sys.exit(0)


def setAsStartupItem():
    """
    将当前程序添加到 Windows 开机启动项。
    """
    global settings
    global isAutoStartServerVar

    # 获取启动目录路径
    startup_folder = os.path.join(
        os.environ.get('APPDATA', ''),
        r'Microsoft\Windows\Start Menu\Programs\Startup'
    )

    if not startup_folder or not os.path.exists(startup_folder):
        logger.error(f"无法获取启动目录: {startup_folder}")
        return

    # 获取当前程序路径
    exe_path = os.path.abspath(sys.argv[0])

    # 快捷方式文件名
    shortcut_name = f"{appLabel}.lnk"
    shortcut_path = os.path.join(startup_folder, shortcut_name)

    try:
        # 使用 WScript.Shell 创建快捷方式
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.Description = f"{appLabel} {appVersion} - 开机启动"
        shortcut.save()

        isAutoStartServerVar.set(True)
        updateSettingVars()
        settings.save()

        logger.info(f"已创建开机启动项: {shortcut_path}")

    except Exception as e:
        logger.error(f"创建开机启动项失败: {e}")


def removeStartupItem():
    """
    删除开机启动项。
    """
    global settings
    global isAutoStartServerVar

    isAutoStartServerVar.set(False)
    updateSettingVars()
    settings.save()

    # 获取启动目录路径
    startup_folder = os.path.join(
        os.environ.get('APPDATA', ''),
        r'Microsoft\Windows\Start Menu\Programs\Startup'
    )

    if not startup_folder:
        logger.warning(f"无法获取启动目录，无法确认开机启动项是否存在")
        return

    # 快捷方式文件名
    shortcut_name = f"{appLabel}.lnk"
    shortcut_path = os.path.join(startup_folder, shortcut_name)

    if not os.path.exists(shortcut_path):
        logger.warning(f"开机启动项不存在: {shortcut_path}")
        return

    try:
        os.remove(shortcut_path)
        logger.info(f"已删除开机启动项: {shortcut_path}")
    except Exception as e:
        logger.error(f"删除开机启动项失败: {e}")


def generateTlsCert():
    """
    生成 TLS/SSL 证书与密钥 [FTPS]。
    等价命令: openssl req -x509 -newkey rsa:2048 -keyout ftpServer.key -out ftpServer.crt -nodes -days 3653
    默认强制覆盖 certFilePath 与 keyFilePath 指向的原有文件。
    """
    global certFilePath
    global keyFilePath

    try:
        # 生成 2048 位 RSA 密钥 (无密码保护, 等价 -nodes)
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        # 构造自签名 X.509 v3 证书
        cert = crypto.X509()
        cert.set_version(2)  # X.509 v3 (0-indexed)
        subject = cert.get_subject()
        subject.CN = "ftpServer"
        subject.O = "JARK006"
        subject.OU = "FtpServer"
        cert.set_serial_number(int(time.time()))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(int(10 * 365.2425 * 24 * 60 * 60))  # 10 年有效期
        cert.set_issuer(subject)  # 自签名, 颁发者与使用者相同
        cert.set_pubkey(key)
        cert.sign(key, "sha256")

        # 覆盖写入
        with open(keyFilePath, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
        with open(certFilePath, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

        logger.info(f"已生成 TLS/SSL 密钥: {keyFilePath}")
        logger.info(f"已生成 TLS/SSL 证书: {certFilePath}")
        logger.info("证书有效期10年，重启服务器后可启用 FTPS [TLS/SSL 显式加密]")

    except Exception as e:
        logger.error(f"生成 TLS/SSL 证书失败: {e}")


def removeTlsCert():
    """
    移除 FTPS TLS/SSL 证书与密钥。
    """
    global certFilePath
    global keyFilePath

    for path, name in [(certFilePath, "证书"), (keyFilePath, "密钥")]:
        try:
            os.remove(path)
            logger.info(f"已移除 TLS/SSL {name}: {path}")
        except FileNotFoundError:
            logger.warning(f"TLS/SSL {name}不存在，无需移除: {path}")
        except Exception as e:
            logger.error(f"移除 TLS/SSL {name}失败: {e}")


def flushLogToWidget(pending: list[str]):
    global loggingWidget
    global logMsgBackup

    loggingWidget.configure(state=tk.NORMAL)
    logMsgBackup.extend(pending)
    if len(logMsgBackup) > 200:
        loggingWidget.delete("1.0", tk.END)
        logMsgBackup = logMsgBackup[-50:]
        loggingWidget.insert(tk.END, "".join(logMsgBackup))
    else:
        loggingWidget.insert(tk.END, "".join(pending))
    loggingWidget.see(tk.END)
    loggingWidget.configure(state=tk.DISABLED)


def logThreadFun():
    global isLogThreadRunning
    global mainWindow

    while isLogThreadRunning:
        try:
            logInfo = logMsg.get(timeout=0.2)
        except queue.Empty:
            continue

        pending = [logInfo]
        while not logMsg.empty():
            try:
                pending.append(logMsg.get_nowait())
            except queue.Empty:
                break

        try:
            mainWindow.after(0, flushLogToWidget, pending)
        except Exception:
            pass


def getTipsAndUrlList() -> tuple[str, list, bool, bool]:
    """
    获取 FTP 服务器的提示信息与 FTP URL 列表，同时判断是否支持 IPv4 与 IPv6
    """
    global settings

    try:
        addrs = socket.getaddrinfo(socket.gethostname(), None)
    except Exception:
        addrs = [(socket.AF_INET, None, None, None, ('127.0.0.1', None))]

    IPv4IPstr = ""
    IPv6IPstr = ""
    IPv4FtpUrlList = []
    IPv6FtpUrlList = []
    ipStrSet = set() # 少数用户存在多个相同IP的情况，避免重复添加

    for item in addrs:
        ipStr = str(item[4][0])

        if ipStr in ipStrSet:
            continue
        ipStrSet.add(ipStr)

        if (settings.IPv6Port > 0) and (":" in ipStr):  # IPv6
            fullUrl = f"ftp://[{ipStr}]" + (
                "" if settings.IPv6Port == 21 else (f":{settings.IPv6Port}")
            )
            IPv6FtpUrlList.append(fullUrl)
            if ipStr.startswith(("fe8", "fe9", "fea", "feb", "fd")):
                IPv6IPstr += f"\n[IPv6 局域网] {fullUrl}"
            elif ipStr[:4] == "240e":
                IPv6IPstr += f"\n[IPv6 电信公网] {fullUrl}"
            elif ipStr[:4] == "2408":
                IPv6IPstr += f"\n[IPv6 联通公网] {fullUrl}"
            elif ipStr[:4] == "2409":
                IPv6IPstr += f"\n[IPv6 移动公网] {fullUrl}"
            else:
                IPv6IPstr += f"\n[IPv6 公网] {fullUrl}"
        elif (settings.IPv4Port > 0) and ("." in ipStr):  # IPv4
            fullUrl = f"ftp://{ipStr}" + (
                "" if settings.IPv4Port == 21 else (f":{settings.IPv4Port}")
            )
            IPv4FtpUrlList.append(fullUrl)
            if is_internal_ip(ipStr):
                IPv4IPstr += f"\n[IPv4 局域网] {fullUrl}"
            elif ipStr.startswith(("198.18.", "28.0.0.")):
                IPv4IPstr += f"\n[IPv4 TUN代理] {fullUrl}"
            else:
                IPv4IPstr += f"\n[IPv4 公网] {fullUrl}"

    ftpUrlList = IPv4FtpUrlList + IPv6FtpUrlList
    tipsStr = myUtils.tipsTitle + IPv4IPstr + IPv6IPstr
    return tipsStr, ftpUrlList, len(IPv4FtpUrlList) > 0, len(IPv6FtpUrlList) > 0


def find_and_activate_window() -> bool:
    """
    查找并激活已运行实例的窗口
    """
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, windowsTitle)
        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
            user32.SetForegroundWindow(hwnd)
            return True
    except Exception as e:
        logger.error(f"激活已运行窗口时出错: {e}")

    return False


def check_single_instance() -> tuple[bool, int]:
    """
    检查是否已有实例运行

    Returns:
        tuple[bool, int]: (是否首次运行, mutex句柄)
                         如果不是首次运行，mutex句柄为0
    """
    mutex_name = f"Local\\{appLabel}_SingleInstance_Mutex"

    try:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()

        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            if find_and_activate_window():
                return False, 0
            else:
                return True, mutex
        elif mutex == 0:
            return True, 0
        else:
            # 首次运行
            return True, mutex

    except Exception as e:
        logger.error(f"单实例检查出错: {e}")
        return True, 0


def main():
    global scaleFactor
    global iconImage
    global settings
    global userList
    global mainWindow
    global loggingWidget
    global logThread
    global tipsTextWidget
    global tipsTextWidgetRightClickMenu
    global directoryCombobox
    global pickDirButton
    global deleteDirButton
    global userNameEntry
    global userPasswordEntry
    global IPv4PortEntry
    global IPv6PortEntry
    global encodingUtf8Radio
    global encodingGbkRadio
    global permReadWriteRadio
    global permReadOnlyRadio
    global isIPv4Supported
    global isIPv6Supported

    global userNameVar
    global userPasswordVar
    global IPv4PortVar
    global IPv6PortVar
    global isReadOnlyVar
    global isGBKVar
    global isAutoStartServerVar
    global isPasswordModified
    global mutex_handle
    global logger

    # 检查单实例
    is_first_instance, mutex_handle = check_single_instance()
    if not is_first_instance:
        # 已有实例运行，退出
        return

    # 告诉操作系统使用程序自身的dpi适配
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

    stdoutRedirectorObj = StdoutRedirector()  # 实例化重定向类
    logThread = threading.Thread(target=logThreadFun)
    logThread.start()

    # 日志配置
    logger = logging.getLogger("ftpserver")
    logger.setLevel(logging.INFO)
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("[%(levelname)1.1s %(asctime)s] %(message)s", datefmt="%H:%M:%S")
    )
    logger.addHandler(_handler)

    mainWindow = tk.Tk()  # 实例化tk对象
    scaleFactor = int(mainWindow.tk.call("tk", "scaling") * 75)
    uiFont = font.Font(
        family="Microsoft YaHei", size=font.nametofont("TkTextFont").cget("size")
    )
    style = ttk.Style(mainWindow)
    style.configure("TButton", width=-5, padding=(scale(8), scale(2)))
    style.configure("TEntry", padding=(scale(2), scale(3)))
    style.configure("TCombobox", padding=(scale(2), scale(3)))
    mainWindow.geometry(f"{scale(600)}x{scale(500)}")
    mainWindow.minsize(scale(600), scale(500))

    ftpIcon = myUtils.IconObj()  # 创建主窗口后才能初始化图标

    mainWindow.title(windowsTitle)
    iconImage = ftpIcon.iconImageTk
    mainWindow.iconphoto(False, iconImage)  # type: ignore
    mainWindow.protocol("WM_DELETE_WINDOW", hideWindow)

    strayMenu = (
        pystray.MenuItem("设为开机启动", setAsStartupItem),
        pystray.MenuItem("取消开机启动", removeStartupItem),
        pystray.MenuItem("生成 TLS/SSL 证书 (启用FTPS)", generateTlsCert),
        pystray.MenuItem("移除 TLS/SSL 证书 (禁用FTPS)", removeTlsCert),
        pystray.MenuItem("显示", showWindow, default=True),
        pystray.MenuItem("退出", handleExit),
    )
    strayIcon = pystray.Icon("FtpServerIcon", ftpIcon.strayIconImage, windowsTitle, strayMenu)
    threading.Thread(target=strayIcon.run, daemon=True).start()

    ttk.Sizegrip(mainWindow).place(relx=1, rely=1, anchor=tk.SE)

    frame1 = ttk.Frame(mainWindow)
    frame1.pack(fill=tk.X, padx=scale(10), pady=(scale(10), scale(5)))

    startButton = ttk.Button(frame1, text="开启", command=startServer)
    startButton.pack(side=tk.LEFT, padx=(0, scale(10)))
    ttk.Button(frame1, text="停止", command=stopServer).pack(
        side=tk.LEFT, padx=(0, scale(10))
    )

    pickDirButton = ttk.Button(frame1, text="选择目录", command=pickDirectory)
    pickDirButton.pack(side=tk.LEFT, padx=(0, scale(10)))

    directoryCombobox = ttk.Combobox(frame1, width=0)
    directoryCombobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

    deleteDirButton = ttk.Button(frame1, text="X", command=deleteCurrentComboboxItem, width=0)
    deleteDirButton.pack(side=tk.LEFT, padx=(0, scale(10)))

    ttk.Button(frame1, text="帮助", command=showHelpWindow, width=-4).pack(
        side=tk.LEFT, padx=(0, scale(5))
    )

    ttk.Button(frame1, text="关于", command=showAboutWindow, width=-4).pack(side=tk.LEFT)

    frame2 = ttk.Frame(mainWindow)
    frame2.pack(fill=tk.X, padx=scale(10), pady=(0, scale(10)))

    userFrame = ttk.Frame(frame2)
    userFrame.pack(side=tk.LEFT, padx=(0, scale(10)), fill=tk.Y)

    ttk.Label(userFrame, text="用户").grid(
        row=0, column=0, pady=(0, scale(5)), padx=(0, scale(5))
    )
    userNameVar = tk.StringVar()
    userNameEntry = ttk.Entry(userFrame, textvariable=userNameVar, width=20)
    userNameEntry.grid(row=0, column=1, sticky=tk.EW, pady=(0, scale(5)))

    ttk.Label(userFrame, text="密码").grid(row=1, column=0, padx=(0, scale(5)))
    userPasswordVar = tk.StringVar()
    userPasswordEntry = ttk.Entry(
        userFrame, textvariable=userPasswordVar, width=20, show="*"
    )
    userPasswordEntry.grid(row=1, column=1, sticky=tk.EW)

    portFrame = ttk.Frame(frame2)
    portFrame.pack(side=tk.LEFT, padx=(0, scale(10)), fill=tk.Y)

    ttk.Label(portFrame, text="IPv4端口").grid(
        row=0, column=0, pady=(0, scale(5)), padx=(0, scale(5))
    )
    IPv4PortVar = tk.StringVar()
    IPv4PortEntry = ttk.Entry(portFrame, textvariable=IPv4PortVar, width=6)
    IPv4PortEntry.grid(row=0, column=1, pady=(0, scale(5)))

    ttk.Label(portFrame, text="IPv6端口").grid(row=1, column=0, padx=(0, scale(5)))
    IPv6PortVar = tk.StringVar()
    IPv6PortEntry = ttk.Entry(portFrame, textvariable=IPv6PortVar, width=6)
    IPv6PortEntry.grid(row=1, column=1)

    encodingFrame = ttk.Frame(frame2)
    encodingFrame.pack(side=tk.LEFT, padx=(0, scale(10)), fill=tk.Y)
    encodingFrame.grid_rowconfigure((0, 1), weight=1)

    isGBKVar = tk.BooleanVar()
    encodingUtf8Radio = ttk.Radiobutton(
        encodingFrame, text="UTF-8 编码", variable=isGBKVar, value=False
    )
    encodingUtf8Radio.grid(row=0, column=0, sticky=tk.EW, pady=(0, scale(5)))
    encodingGbkRadio = ttk.Radiobutton(encodingFrame, text="GBK 编码", variable=isGBKVar, value=True)
    encodingGbkRadio.grid(row=1, column=0, sticky=tk.EW)

    permissionFrame = ttk.Frame(frame2)
    permissionFrame.pack(side=tk.LEFT, padx=(0, scale(10)), fill=tk.Y)
    permissionFrame.grid_rowconfigure((0, 1), weight=1)

    isReadOnlyVar = tk.BooleanVar()
    permReadWriteRadio = ttk.Radiobutton(
        permissionFrame, text="读写", variable=isReadOnlyVar, value=False
    )
    permReadWriteRadio.grid(row=0, column=0, sticky=tk.EW, pady=(0, scale(5)))
    permReadOnlyRadio = ttk.Radiobutton(
        permissionFrame, text="只读", variable=isReadOnlyVar, value=True
    )
    permReadOnlyRadio.grid(row=1, column=0, sticky=tk.EW)

    isAutoStartServerVar = tk.BooleanVar()
    ttk.Checkbutton(
        frame2,
        text="下次打开软件后自动\n隐藏窗口并启动服务",
        variable=isAutoStartServerVar,
        onvalue=True,
        offvalue=False,
    ).pack(side=tk.LEFT)

    tipsTextWidget = scrolledtext.ScrolledText(
        mainWindow, bg="#dddddd", wrap=tk.CHAR, font=uiFont, height=10, width=0
    )
    tipsTextWidget.pack(fill=tk.BOTH, expand=False, padx=scale(10), pady=(0, scale(10)))

    loggingWidget = scrolledtext.ScrolledText(
        mainWindow, bg="#dddddd", wrap=tk.CHAR, font=uiFont, height=0, width=0
    )
    loggingWidget.pack(fill=tk.BOTH, expand=True, padx=scale(10), pady=(0, scale(10)))
    loggingWidget.configure(state=tk.DISABLED)

    settings = Settings.Settings()
    userList = UserList.UserList()
    if not userList.isEmpty():
        userList.printUserList()

    directoryCombobox["value"] = tuple(settings.directoryList)
    directoryCombobox.current(0)

    userNameVar.set(settings.userName)
    isPasswordModified = False
    userPasswordVar.set("******" if len(settings.userPassword) > 0 else "")
    userPasswordVar.trace_add("write", lambda *_: onPasswordChanged())
    IPv4PortVar.set("" if settings.IPv4Port == 0 else str(settings.IPv4Port))
    IPv6PortVar.set("" if settings.IPv6Port == 0 else str(settings.IPv6Port))
    isGBKVar.set(settings.isGBK)
    isReadOnlyVar.set(settings.isReadOnly)
    isAutoStartServerVar.set(settings.isAutoStartServer)

    tipsStr, ftpUrlList, isIPv4Supported, isIPv6Supported = getTipsAndUrlList()
    tipsTextWidget.insert(tk.INSERT, tipsStr)
    tipsTextWidget.configure(state=tk.DISABLED)

    tipsTextWidgetRightClickMenu = tk.Menu(mainWindow, tearoff=False)
    for url in ftpUrlList:
        tipsTextWidgetRightClickMenu.add_command(
            label=f"复制 {url}", command=lambda url=url: copyToClipboard(url)
        )

    tipsTextWidget.bind(
        "<Button-3>",
        lambda event: tipsTextWidgetRightClickMenu.post(event.x_root, event.y_root),
    )

    if settings.isAutoStartServer:
        startButton.invoke()
        mainWindow.withdraw()

    if os.path.exists(certFilePath) and os.path.exists(keyFilePath):
        logger.info("检测到 TLS/SSL 证书文件, 默认使用 FTPS [TLS/SSL显式加密]")

    mainWindow.mainloop()


if __name__ == "__main__":
    main()
