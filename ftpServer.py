r"""
FTP Server with GUI Interface
一个带图形界面的FTP服务器

Author: JARK006
Email: jark006@qq.com
Github: https://github.com/jark006
Project: https://github.com/jark006/FtpServer
License: MIT License
Copyright (c) 2025 JARK006

# 打包工具
    pip install pyinstaller nuitka

# 第三方库需求
    pip install Pillow pypiwin32 pystray pyopenssl pyasynchat

# 在终端中生成SSL证书 (ftpServer.key, ftpServer.crt 有效期100年) 放到程序所在目录则自动启用 FTPS [TLS/SSL显式加密, TLSv1.3]
    openssl req -x509 -newkey rsa:2048 -keyout ftpServer.key -out ftpServer.crt -nodes -days 36500

# 打包 单文件 隐藏终端窗口 以下三选一 (第一条和第二条是同一个，第一条执行过一次产生ftpServer.spec后，以后只需执行第二条)
    pyinstaller.exe -F -w .\ftpServer.py -i .\ftpServer.ico --version-file .\file_version_info.txt
    pyinstaller.exe .\ftpServer.spec
    python -m nuitka .\ftpServer.py --windows-icon-from-ico=.\ftpServer.ico --standalone --lto=yes --enable-plugin=tk-inter --windows-console-mode=disable --company-name=JARK006 --product-name=ftpServer --file-version=1.24.0.0 --product-version=1.24.0.0 --file-description="FtpServer Github@JARK006" --copyright="Copyright (C) 2025 Github@JARK006"

"""

# 标准库导入
import os
import queue
import socket
import sys
import threading
import time
import ctypes
import functools

# GUI相关导入
import tkinter as tk
import webbrowser
from tkinter import ttk, scrolledtext, filedialog, messagebox, font

# 第三方库导入
import pystray
import win32clipboard
import win32con

# 本地模块导入
import Settings
import UserList
import myUtils

# 汉化 pyftpdlib 模块导入
from mypyftpdlib.authorizers import DummyAuthorizer
from mypyftpdlib.handlers import FTPHandler, TLS_FTPHandler
from mypyftpdlib.servers import ThreadedFTPServer

appLabel = "FTP文件服务器"
appVersion = "v1.24"
appAuthor = "JARK006"
githubLink = "https://github.com/jark006/FtpServer"
releaseLink = "https://github.com/jark006/FtpServer/releases"
quarkLink = "https://pan.quark.cn/s/fb740c256653"
baiduLink = "https://pan.baidu.com/s/1955qjdrnPtxhNhtksjqvfg?pwd=6666"
windowsTitle = f"{appLabel} {appVersion}"
tipsTitle = "若用户名空白则默认匿名访问(anonymous)。若中文乱码则需更换编码方式, 再重启服务。若无需开启IPv6只需将其端口留空即可, IPv4同理。请设置完后再开启服务。若需FTPS或多用户配置, 请点击“帮助”按钮查看使用说明。以下为本机所有IP地址(含所有物理网卡/虚拟网卡), 右键可复制。\n"

logMsg = queue.Queue()
logThreadrunning: bool = True

permReadOnly: str = "elr"
permReadWrite: str = "elradfmwMT"

isIPv4Supported: bool = False
isIPv6Supported: bool = False
isIPv4ThreadRunning: bool = False
isIPv6ThreadRunning: bool = False

certFilePath = os.path.join(os.path.dirname(sys.argv[0]), "ftpServer.crt")
keyFilePath = os.path.join(os.path.dirname(sys.argv[0]), "ftpServer.key")

ScaleFactor = 100


def scale(n: int) -> int:
    global ScaleFactor
    return int(n * ScaleFactor / 100)


def showHelp():
    global window
    global iconImage
    global uiFont
    helpTips = """以下是 安全加密连接FTPS 和 多用户配置 说明, 普通用户一般不需要。

==== FTPS 配置 ====

本软件默认使用 FTP 明文传输数据，如果数据比较敏感，或者网络环境不安全，则可以按以下步骤开启 FTPS 加密传输数据。

在 "Linux" 或 "MinGW64" 终端使用 "openssl" (命令如下，需填入一些简单信息: 地区/名字/Email等)生成SSL证书文件(ftpServer.key和ftpServer.crt), "不要重命名"文件为其他名称。

openssl req -x509 -newkey rsa:2048 -keyout ftpServer.key -out ftpServer.crt -nodes -days 36500

直接将 ftpServer.key 和 ftpServer.crt 放到程序所在目录, 开启服务时若存在这两个文件, 则启用加密传输 "FTPS [TLS/SSL显式加密, TLSv1.3]"。
Windows文件管理器对 显式FTPS 支持不佳, 推荐使用开源软件 "WinSCP" FTP客户端, 对 FTPS 支持比较好。
开启 "FTPS 加密传输" 后, 会影响传输性能, 最大传输速度会降到 50MiB/s 左右。若对网络安全没那么高要求, 不建议加密。


==== 多用户配置 ====

一般单人使用时，只需在软件主页面设置用户名和密码即可。如果需要开放给多人使用，可以按以下步骤建立多个用户，分配不同的读写权限和根目录。

在主程序所在目录新建文件 "FtpServerUserList.csv" , 使用 "Excel"或文本编辑器(需熟悉csv文件格式)编辑, 一行一个配置: 
第一列: 用户名, 限定英文大小写/数字。
第二列: 密码, 限定英文大小写/数字/符号。
第三列: 权限, 详细配置如下。
第四列: 根目录路径。

例如:
| JARK006   | 123456 | readonly  | D:/Downloads |
| JARK007   | 456789 | readwrite | D:/Data      |
| JARK008   | abc123 | 只读      | D:/FtpRoot   |
| JARK009   | abc456 | elr       | D:/FtpRoot   |
| anonymous |        | elr       | D:/FtpRoot   |
| ...       |        |           |              |
注: anonymous 是匿名用户, 允许不设密码, 其他用户必须设置密码。

权限配置: 
使用 "readonly" 或 "只读" 设置为 "只读权限"。
使用 "readwrite" 或 "读写" 设置为 "读写权限"。
使用 "自定义" 权限设置, 从以下权限挑选自行组合(注意大小写)。

参考链接: https://pyftpdlib.readthedocs.io/en/latest/api.html#pyftpdlib.authorizers.DummyAuthorizer.add_user

读取权限: 
 "e" = 更改目录 (CWD 命令)
 "l" = 列出文件 (LIST、NLST、STAT、MLSD、MLST、SIZE、MDTM 命令)
 "r" = 从服务器检索文件 (RETR 命令)

写入权限: 
 "a" = 将数据附加到现有文件 (APPE 命令)
 "d" = 删除文件或目录 (DELE、RMD 命令)
 "f" = 重命名文件或目录 (RNFR、RNTO 命令)
 "m" = 创建目录 (MKD 命令)
 "w" = 将文件存储到服务器 (STOR、STOU 命令)
 "M" = 更改文件模式 (SITE CHMOD 命令)
 "T" = 更新文件上次修改时间 (MFMT 命令)

其他:
1. 若读取到有效配置, 则自动 "禁用"主页面的用户/密码设置。
2. 密码不要出现英文逗号 "," 字符, 以免和csv文本格式冲突。
3. 若临时不需多用户配置, 可将配置文件 "删除" 或 "重命名" 为其他名称。
4. 配置文件可以是UTF-8或GBK编码。
"""

    helpWindows = tk.Toplevel(window)
    helpWindows.geometry(f"{scale(600)}x{scale(500)}")
    helpWindows.minsize(scale(600), scale(500))
    helpWindows.title("帮助")
    helpWindows.iconphoto(False, iconImage)  # type: ignore
    helpTextWidget = scrolledtext.ScrolledText(
        helpWindows, bg="#dddddd", wrap=tk.CHAR, font=uiFont, width=0, height=0
    )
    helpTextWidget.insert(tk.INSERT, helpTips)
    helpTextWidget.configure(state=tk.DISABLED)
    helpTextWidget.pack(fill=tk.BOTH, expand=True)

    menu = tk.Menu(window, tearoff=False)
    menu.add_command(
        label="复制",
        command=lambda event=None: helpTextWidget.event_generate("<<Copy>>"),
    )
    helpTextWidget.bind(
        "<Button-3>", lambda event: menu.post(event.x_root, event.y_root)
    )


def showAbout():
    global window
    global iconImage

    aboutWindows = tk.Toplevel(window)
    # 自动跟随内容调节大小，适配大字体
    # aboutWindows.geometry(f"{scale(400)}x{scale(200)}")
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
    tk.Label(linksFrame, text="夸克网盘").grid(row=2, column=0)
    tk.Label(linksFrame, text="百度云盘").grid(row=3, column=0)

    label1 = ttk.Label(linksFrame, text=githubLink, foreground="blue")
    label1.bind("<Button-1>", lambda event: webbrowser.open(githubLink))
    label1.grid(row=0, column=1, sticky=tk.W)

    label2 = ttk.Label(linksFrame, text=releaseLink, foreground="blue")
    label2.bind("<Button-1>", lambda event: webbrowser.open(releaseLink))
    label2.grid(row=1, column=1, sticky=tk.W)

    label3 = ttk.Label(linksFrame, text=quarkLink, foreground="blue")
    label3.bind("<Button-1>", lambda event: webbrowser.open(quarkLink))
    label3.grid(row=2, column=1, sticky=tk.W)

    baiduLinkTmp = baiduLink[:30] + "... 提取码: 6666"
    label4 = ttk.Label(linksFrame, text=baiduLinkTmp, foreground="blue")
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
        print("目录列表已清空, 默认恢复到程序所在目录")
        return

    currentValue = directoryCombobox.get()

    if currentValue in currentDirectoryList:
        currentIdx = directoryCombobox.current(None)
        currentDirectoryList.remove(currentValue)
        settings.directoryList = currentDirectoryList
        directoryCombobox["value"] = tuple(currentDirectoryList)
        if currentIdx >= len(currentDirectoryList):
            directoryCombobox.current(len(currentDirectoryList) - 1)
        else:
            directoryCombobox.current(currentIdx)
    else:
        directoryCombobox.current(0)


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
    if len(passwordTmp) == 0:
        settings.userPassword = ""
    elif passwordTmp == "******":
        pass
    else:
        settings.userPassword = Settings.Settings.encry2sha256(passwordTmp)
        userPasswordVar.set("******")

    try:
        IPv4PortInt = 0 if IPv4PortVar.get() == "" else int(IPv4PortVar.get())
        if 0 <= IPv4PortInt and IPv4PortInt < 65536:
            settings.IPv4Port = IPv4PortInt
        else:
            raise
    except:
        tips: str = (
            f"当前 IPv4 端口值: [ {IPv4PortVar.get()} ] 异常, 正常范围: 1 ~ 65535, 已重设为: 21"
        )
        messagebox.showwarning("IPv4 端口值异常", tips)
        print(tips)
        settings.IPv4Port = 21
        IPv4PortVar.set("21")

    try:
        IPv6PortInt = 0 if IPv6PortVar.get() == "" else int(IPv6PortVar.get())
        if 0 <= IPv6PortInt and IPv6PortInt < 65536:
            settings.IPv6Port = IPv6PortInt
        else:
            raise
    except:
        tips: str = (
            f"当前 IPv6 端口值: [ {IPv6PortVar.get()} ] 异常, 正常范围: 1 ~ 65535, 已重设为: 21"
        )
        messagebox.showwarning("IPv6 端口值异常", tips)
        print(tips)
        settings.IPv6Port = 21
        IPv6PortVar.set("21")


class myStdout:  # 重定向输出
    def __init__(self):
        sys.stdout = self
        sys.stderr = self

    def write(self, info):
        logMsg.put(info)

    def flush(self):
        pass


def copyToClipboard(text: str):
    if len(text) > 0:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
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
    global userNameEntry
    global userPasswordEntry
    global serverThreadV4
    global serverThreadV6
    global isIPv4Supported
    global isIPv6Supported
    global isIPv4ThreadRunning
    global isIPv6ThreadRunning
    global tipsTextWidget
    global tipsTextWidgetRightClickMenu

    if isIPv4ThreadRunning:
        print("[FTP IPv4] 正在运行")
        return
    if isIPv6ThreadRunning:
        print("[FTP IPv6] 正在运行")
        return

    updateSettingVars()

    if not os.path.exists(settings.directoryList[0]):
        tips: str = (
            f"路径: [ {settings.directoryList[0]} ]异常！请检查路径是否正确或者有没有读取权限。"
        )
        messagebox.showerror("路径异常", tips)
        print(tips)
        return

    userList.load()
    if userList.isEmpty():
        userNameEntry.configure(state=tk.NORMAL)
        userPasswordEntry.configure(state=tk.NORMAL)
        if len(settings.userName) > 0 and len(settings.userPassword) == 0:
            tips: str = "!!! 请设置密码再启动服务 !!!"
            messagebox.showerror("密码异常", tips)
            print(tips)
            return
        if (
            settings.userName == "anonymous" or len(settings.userName) == 0
        ) and settings.isReadOnly == False:
            print(
                "警告：当前允许【匿名用户】登录，且拥有【写入、修改】文件权限，请谨慎对待。"
            )
            print(
                "若是安全的内网环境可忽略以上警告，否则【匿名用户】应当选择【只读】权限。"
            )
    else:
        userNameEntry.configure(state=tk.DISABLED)
        userPasswordEntry.configure(state=tk.DISABLED)

    tipsStr, ftpUrlList = getTipsAndUrlList()

    if len(ftpUrlList) == 0:
        tips: str = "!!! 本机没有检测到网络IP, 请检查端口设置或网络连接, 或稍后重试 !!!"
        messagebox.showerror("网络或端口设置异常", tips)
        print(tips)
        return

    settings.save()

    tipsTextWidget.configure(state=tk.NORMAL)
    tipsTextWidget.delete("0.0", tk.END)
    tipsTextWidget.insert(tk.INSERT, tipsStr)
    tipsTextWidget.configure(state=tk.DISABLED)

    tipsTextWidgetRightClickMenu.delete(0, tk.END)
    for url in ftpUrlList:
        tipsTextWidgetRightClickMenu.add_command(
            label=f"复制 {url}", command=lambda url=url: copyToClipboard(url)
        )

    try:
        hasStartServer: bool = False
        if isIPv4Supported and settings.IPv4Port > 0:
            serverThreadV4 = threading.Thread(target=serverThreadFun, args=("IPv4",))
            serverThreadV4.start()
            hasStartServer = True

        if isIPv6Supported and settings.IPv6Port > 0:
            serverThreadV6 = threading.Thread(target=serverThreadFun, args=("IPv6",))
            serverThreadV6.start()
            hasStartServer = True

        if not hasStartServer:
            tips: str = "!!! 未检测到有效端口, 服务无法启动, 请检查端口设置是否正确 !!!"
            messagebox.showerror("端口异常", tips)
            print(tips)
            return

    except Exception as e:
        tips: str = f"!!! 发生异常, 无法启动线程 !!!\n{e}"
        messagebox.showerror("启动异常", tips)
        print(tips)
        return

    if userList.isEmpty():
        print(
            "\n用户: {}\n密码: {}\n权限: {}\n编码: {}\n目录: {}\n".format(
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
        userList.print()
        print(f"编码: {'GBK' if settings.isGBK else 'UTF-8'}\n")


def serverThreadFun(IP_Family: str):
    global serverV4
    global isIPv4ThreadRunning
    global serverV6
    global isIPv6ThreadRunning
    global certFilePath
    global keyFilePath

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

    if os.path.exists(certFilePath) and os.path.exists(keyFilePath):
        handler = TLS_FTPHandler
        handler.certfile = certFilePath  # type: ignore
        handler.keyfile = keyFilePath  # type: ignore
        handler.tls_control_required = True
        handler.tls_data_required = True
        print(
            "[FTP IPv4] 已加载 SSL 证书文件, 默认开启 FTPS [TLS/SSL显式加密, TLSv1.3]"
        )
    else:
        handler = FTPHandler

    handler.authorizer = authorizer
    handler.encoding = "gbk" if settings.isGBK else "utf8"
    if IP_Family == "IPv4":
        serverV4 = ThreadedFTPServer(("0.0.0.0", settings.IPv4Port), handler)
        print("[FTP IPv4] 开始运行")
        isIPv4ThreadRunning = True
        serverV4.serve_forever()
        isIPv4ThreadRunning = False
        print("[FTP IPv4] 已关闭")
    else:
        serverV6 = ThreadedFTPServer(("::", settings.IPv6Port), handler)
        print("[FTP IPv6] 开始运行")
        isIPv6ThreadRunning = True
        serverV6.serve_forever()
        isIPv6ThreadRunning = False
        print("[FTP IPv6] 已关闭")


def closeServer():
    global serverV4
    global serverV6
    global serverThreadV4
    global serverThreadV6
    global isIPv4ThreadRunning
    global isIPv6ThreadRunning
    global isIPv4Supported
    global isIPv6Supported

    if isIPv4Supported and settings.IPv4Port > 0:
        if isIPv4ThreadRunning:
            print("[FTP IPv4] 正在关闭...")
            serverV4.close_all()  # 注意: 这也会关闭serverV6的所有连接
            serverThreadV4.join()
        print("[FTP IPv4] 线程已关闭")

    if isIPv6Supported and settings.IPv6Port > 0:
        if isIPv6ThreadRunning:
            print("[FTP IPv6] 正在关闭...")
            serverV6.close_all()
            serverThreadV6.join()
        print("[FTP IPv6] 线程已关闭")


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
        messagebox.showerror("路径异常", tips)
        print(tips)


def showWindow():
    global window
    window.deiconify()


def hideWindow():
    global window
    window.withdraw()


def handleExit(strayIcon: pystray._base.Icon):
    global window
    global logThreadrunning
    global logThread

    updateSettingVars()
    settings.save()

    closeServer()
    strayIcon.stop()

    print("等待日志线程退出...")
    logThreadrunning = False
    logThread.join()

    window.destroy()
    exit(0)


def logThreadFun():
    global logThreadrunning
    global loggingWidget

    logMsgBackup = []
    while logThreadrunning:
        if logMsg.empty():
            time.sleep(0.1)
            continue

        logInfo = ""
        while not logMsg.empty():
            logInfo += logMsg.get()

        logMsgBackup.append(logInfo)
        if len(logMsgBackup) > 500:
            loggingWidget.configure(state=tk.NORMAL)
            loggingWidget.delete(0.0, tk.END)
            loggingWidget.configure(state=tk.DISABLED)

            logMsgBackup = logMsgBackup[-20:]
            logInfo = ""
            for tmp in logMsgBackup:
                logInfo += tmp

        loggingWidget.configure(state=tk.NORMAL)
        loggingWidget.insert(tk.END, logInfo)
        loggingWidget.see(tk.END)
        loggingWidget.configure(state=tk.DISABLED)


def getTipsAndUrlList():
    global isIPv4Supported
    global isIPv6Supported
    global tipsTitle

    addrs = socket.getaddrinfo(socket.gethostname(), None)

    IPv4IPstr = ""
    IPv6IPstr = ""
    IPv4FtpUrlList = []
    IPv6FtpUrlList = []
    for item in addrs:
        ipStr = str(item[4][0])
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
                IPv6IPstr += f"\n[IPv6 移动铁通公网] {fullUrl}"
            else:
                IPv6IPstr += f"\n[IPv6 公网] {fullUrl}"
        elif (settings.IPv4Port > 0) and ("." in ipStr):  # IPv4
            fullUrl = f"ftp://{ipStr}" + (
                "" if settings.IPv4Port == 21 else (f":{settings.IPv4Port}")
            )
            IPv4FtpUrlList.append(fullUrl)
            if is_internal_ip(ipStr):
                IPv4IPstr += f"\n[IPv4 局域网] {fullUrl}"
            else:
                IPv4IPstr += f"\n[IPv4 公网] {fullUrl}"

    isIPv4Supported = len(IPv4FtpUrlList) > 0
    isIPv6Supported = len(IPv6FtpUrlList) > 0

    ftpUrlList = IPv4FtpUrlList + IPv6FtpUrlList
    tipsStr = tipsTitle + IPv4IPstr + IPv6IPstr
    return tipsStr, ftpUrlList


def main():
    global ScaleFactor
    global iconImage
    global uiFont
    global settings
    global userList
    global window
    global loggingWidget
    global logThread
    global tipsTextWidget
    global tipsTextWidgetRightClickMenu
    global directoryCombobox
    global userNameEntry
    global userPasswordEntry

    global userNameVar
    global userPasswordVar
    global IPv4PortVar
    global IPv6PortVar
    global isReadOnlyVar
    global isGBKVar
    global isAutoStartServerVar

    # 告诉操作系统使用程序自身的dpi适配
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

    mystd = myStdout()  # 实例化重定向类
    logThread = threading.Thread(target=logThreadFun)
    logThread.start()

    window = tk.Tk()  # 实例化tk对象
    ScaleFactor = window.tk.call("tk", "scaling") * 75
    uiFont = font.Font(
        family="Consolas", size=font.nametofont("TkTextFont").cget("size")
    )
    style = ttk.Style(window)
    style.configure("TButton", width=-5, padding=(scale(8), scale(2)))
    style.configure("TEntry", padding=(scale(2), scale(3)))
    style.configure("TCombobox", padding=(scale(2), scale(3)))
    window.geometry(f"{scale(600)}x{scale(500)}")
    window.minsize(scale(600), scale(500))

    ftpIcon = myUtils.iconObj()  # 创建主窗口后才能初始化图标

    window.title(windowsTitle)
    iconImage = ftpIcon.iconImageTk
    window.iconphoto(False, iconImage)  # type: ignore
    window.protocol("WM_DELETE_WINDOW", hideWindow)

    strayMenu = (
        pystray.MenuItem("显示", showWindow, default=True),
        pystray.MenuItem("退出", handleExit),
    )
    strayIcon = pystray.Icon("icon", ftpIcon.strayIconImage, windowsTitle, strayMenu)
    threading.Thread(target=strayIcon.run, daemon=True).start()

    ttk.Sizegrip(window).place(relx=1, rely=1, anchor=tk.SE)

    frame1 = ttk.Frame(window)
    frame1.pack(fill=tk.X, padx=scale(10), pady=(scale(10), scale(5)))

    startButton = ttk.Button(frame1, text="开启", command=startServer)
    startButton.pack(side=tk.LEFT, padx=(0, scale(10)))
    ttk.Button(frame1, text="关闭", command=closeServer).pack(
        side=tk.LEFT, padx=(0, scale(10))
    )

    ttk.Button(frame1, text="选择目录", command=pickDirectory).pack(
        side=tk.LEFT, padx=(0, scale(10))
    )

    directoryCombobox = ttk.Combobox(frame1, width=0)
    directoryCombobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

    ttk.Button(frame1, text="X", command=deleteCurrentComboboxItem, width=0).pack(
        side=tk.LEFT, padx=(0, scale(10))
    )

    ttk.Button(frame1, text="帮助", command=showHelp, width=-4).pack(
        side=tk.LEFT, padx=(0, scale(5))
    )

    ttk.Button(frame1, text="关于", command=showAbout, width=-4).pack(side=tk.LEFT)

    frame2 = ttk.Frame(window)
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
    ttk.Entry(portFrame, textvariable=IPv4PortVar, width=6).grid(
        row=0, column=1, pady=(0, scale(5))
    )

    ttk.Label(portFrame, text="IPv6端口").grid(row=1, column=0, padx=(0, scale(5)))
    IPv6PortVar = tk.StringVar()
    ttk.Entry(portFrame, textvariable=IPv6PortVar, width=6).grid(row=1, column=1)

    encodingFrame = ttk.Frame(frame2)
    encodingFrame.pack(side=tk.LEFT, padx=(0, scale(10)), fill=tk.Y)
    encodingFrame.grid_rowconfigure((0, 1), weight=1)

    isGBKVar = tk.BooleanVar()
    ttk.Radiobutton(
        encodingFrame, text="UTF-8 编码", variable=isGBKVar, value=False
    ).grid(row=0, column=0, sticky=tk.EW, pady=(0, scale(5)))
    ttk.Radiobutton(encodingFrame, text="GBK 编码", variable=isGBKVar, value=True).grid(
        row=1, column=0, sticky=tk.EW
    )

    permissionFrame = ttk.Frame(frame2)
    permissionFrame.pack(side=tk.LEFT, padx=(0, scale(10)), fill=tk.Y)
    permissionFrame.grid_rowconfigure((0, 1), weight=1)

    isReadOnlyVar = tk.BooleanVar()
    ttk.Radiobutton(
        permissionFrame, text="读写", variable=isReadOnlyVar, value=False
    ).grid(row=0, column=0, sticky=tk.EW, pady=(0, scale(5)))
    ttk.Radiobutton(
        permissionFrame, text="只读", variable=isReadOnlyVar, value=True
    ).grid(row=1, column=0, sticky=tk.EW)

    isAutoStartServerVar = tk.BooleanVar()
    ttk.Checkbutton(
        frame2,
        text="下次打开软件后自动\n隐藏窗口并启动服务",
        variable=isAutoStartServerVar,
        onvalue=True,
        offvalue=False,
    ).pack(side=tk.LEFT)

    tipsTextWidget = scrolledtext.ScrolledText(
        window, bg="#dddddd", wrap=tk.CHAR, font=uiFont, height=10, width=0
    )
    tipsTextWidget.pack(fill=tk.BOTH, expand=False, padx=scale(10), pady=(0, scale(10)))

    loggingWidget = scrolledtext.ScrolledText(
        window, bg="#dddddd", wrap=tk.CHAR, font=uiFont, height=0, width=0
    )
    loggingWidget.pack(fill=tk.BOTH, expand=True, padx=scale(10), pady=(0, scale(10)))
    loggingWidget.configure(state=tk.DISABLED)

    settings = Settings.Settings()
    userList = UserList.UserList()
    if not userList.isEmpty():
        userList.print()
        userNameEntry.configure(state=tk.DISABLED)
        userPasswordEntry.configure(state=tk.DISABLED)

    directoryCombobox["value"] = tuple(settings.directoryList)
    directoryCombobox.current(0)

    userNameVar.set(settings.userName)
    userPasswordVar.set("******" if len(settings.userPassword) > 0 else "")
    IPv4PortVar.set("" if settings.IPv4Port == 0 else str(settings.IPv4Port))
    IPv6PortVar.set("" if settings.IPv6Port == 0 else str(settings.IPv6Port))
    isGBKVar.set(settings.isGBK)
    isReadOnlyVar.set(settings.isReadOnly)
    isAutoStartServerVar.set(settings.isAutoStartServer)

    tipsStr, ftpUrlList = getTipsAndUrlList()
    tipsTextWidget.insert(tk.INSERT, tipsStr)
    tipsTextWidget.configure(state=tk.DISABLED)

    tipsTextWidgetRightClickMenu = tk.Menu(window, tearoff=False)
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
        window.withdraw()

    if os.path.exists(certFilePath) and os.path.exists(keyFilePath):
        print("检测到 SSL 证书文件, 默认使用 FTPS [TLS/SSL显式加密, TLSv1.3]")

    window.mainloop()


if __name__ == "__main__":
    main()
