import socket, sys, os, queue, time, base64, threading, ctypes, webbrowser, pystray

import Settings
import UserList
import win32clipboard
import win32con
import tkinter

from tkinter import ttk, scrolledtext, filedialog, messagebox, font
from mypyftpdlib.authorizers import DummyAuthorizer
from mypyftpdlib.handlers import FTPHandler, TLS_FTPHandler
from mypyftpdlib.servers import ThreadedFTPServer
from PIL import ImageTk, Image
from io import BytesIO
from functools import reduce

# pip install Pillow pypiwin32 pyinstaller nuitka pystray pyopenssl pyasynchat

# 在终端中生成SSL证书 (ftpServer.key, ftpServer.crt 有效期100年) 放到程序所在目录则自动启用 FTPS [TLS/SSL显式加密, TLSv1.3]
# $> openssl req -x509 -newkey rsa:2048 -keyout ftpServer.key -out ftpServer.crt -nodes -days 36500

# 打包 单文件 隐藏终端窗口
# pyinstaller.exe -F -w .\ftpServer.py -i .\ftpServer.ico --version-file .\file_version_info.txt
# pyinstaller.exe .\ftpServer.spec
# python -m nuitka --standalone --onefile --lto=yes --enable-plugin=tk-inter --windows-console-mode=disable .\ftpServer.py --windows-icon-from-ico=.\ftpServer.ico --company-name=JARK006 --product-name=ftpServer --file-version=1.21.0.0 --product-version=1.21.0.0 --file-description="FtpServer Github@JARK006" --copyright="Copyright (C) 2024"


appLabel = "FTP文件服务器"
appVersion = "v1.21"
appAuthor = "JARK006"
githubLink = "https://github.com/jark006/FtpServer"
releaseLink = "https://github.com/jark006/FtpServer/releases"
quarkLink = "https://pan.quark.cn/s/fb740c256653"
baiduLink = "https://pan.baidu.com/s/1955qjdrnPtxhNhtksjqvfg?pwd=6666"
windowsTitle = f"{appLabel} {appVersion}"
tipsTitle = "若用户名空白则默认匿名访问(anonymous)。若中文乱码则需更换编码方式, 再重启服务。请设置完后再开启服务。若需FTPS或多用户配置, 请点击“帮助”按钮查看使用说明。以下为本机所有IP地址(含所有物理网卡/虚拟网卡), 右键可复制。\n"

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

"""
import base64
with open(r"ico64x64.ico", "rb") as f:
    iconStr = base64.b64encode(f.read())
    print(iconStr)
"""
iconStr = b"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"


def scale(n: int) -> int:
    global ScaleFactor
    return int(n * ScaleFactor / 100)


def showHelp():
    global window
    global iconImage
    global uiFont
    helpTips = """以下是 安全加密连接FTPS 和 多用户配置 说明, 普通用户一般不需要。

==== FTPS 配置 ====

在 "Linux" 或 "MinGW64" 终端使用 "openssl" (命令如下，需填入一些简单信息: 地区/名字/Email等)生成SSL证书文件(ftpServer.key和ftpServer.crt), "不要重命名"文件为其他名称。

openssl req -x509 -newkey rsa:2048 -keyout ftpServer.key -out ftpServer.crt -nodes -days 36500

直接将 ftpServer.key 和 ftpServer.crt 放到程序所在目录, 开启服务时若存在这两个文件, 则启用加密传输 "FTPS [TLS/SSL显式加密, TLSv1.3]"。
Windows文件管理器对 显式FTPS 支持不佳, 推荐使用开源软件 "WinSCP" FTP客户端, 对 FTPS 支持比较好。
开启 "FTPS 加密传输" 后, 会影响传输性能, 最大传输速度会降到 50MiB/s 左右。若对网络安全没那么高要求, 不建议加密。


==== 多用户配置 ====

在主程序所在目录新建文件 "FtpServerUserList.csv" , 使用 "Excel"或文本编辑器(需熟悉csv文件格式)编辑, 一行一个配置: 
第一列: 用户名, 限定英文大小写/数字。
第二列: 密码, 限定英文大小写/数字/符号。
第三列: 权限, 详细配置如下。
第四列: 根目录路径。

详细权限配置: 
使用 "readonly" 或 "只读" 设置为 "只读权限"。
使用 "readwrite" 或 "读写" 设置为 "读写权限"。
使用 "自定义" 权限设置, 从以下权限挑选自行组合(注意大小写): 

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
    

例如:
| JARK006   | 123456 | readonly  | D:\\Downloads |
| JARK007   | 456789 | readwrite | D:\\Data      |
| JARK008   | abc123 | 只读      | D:\\FtpRoot   |
| JARK009   | abc456 | elr       | D:\\FtpRoot   |
| anonymous |        | elr       | D:\\FtpRoot   |
| ...       |        |           |              |
注: anonymous 是匿名用户, 允许不设密码, 其他用户必须设置密码。

其他:
1. 若读取到有效配置, 则自动 "禁用"主页面的用户/密码设置。
2. 密码不要出现英文逗号 "," 字符, 以免和csv文本格式冲突。
3. 若临时不需多用户配置, 可将配置文件 "删除" 或 "重命名" 为其他名称。
4. 配置文件可以是UTF-8或GBK编码。
"""

    helpWindows = tkinter.Toplevel(window)
    helpWindows.geometry(f"{scale(600)}x{scale(500)}")
    helpWindows.resizable(False, False)
    helpWindows.title("帮助")
    helpWindows.iconphoto(False, iconImage)
    helpTextWidget = scrolledtext.ScrolledText(
        helpWindows, bg="#dddddd", wrap=tkinter.CHAR, font=uiFont
    )
    helpTextWidget.insert(tkinter.INSERT, helpTips)
    helpTextWidget.configure(state=tkinter.DISABLED)
    helpTextWidget.place(x=0, y=0, width=scale(600), height=scale(500))

    menu = tkinter.Menu(window, tearoff=False)
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

    aboutWindows = tkinter.Toplevel(window)
    aboutWindows.geometry(f"{scale(400)}x{scale(200)}")
    aboutWindows.resizable(False, False)
    aboutWindows.title("关于")
    aboutWindows.iconphoto(False, iconImage)

    tkinter.Label(aboutWindows, image=iconImage).place(
        x=scale(0), y=scale(0), width=scale(100), height=scale(100)
    )
    tkinter.Label(
        aboutWindows,
        text=f"{appLabel} {appVersion}",
        font=font.Font(font=("Consolas", scale(12))),
    ).place(x=scale(100), y=scale(0), width=scale(300), height=scale(70))

    tkinter.Label(aboutWindows, text=f"开发者: {appAuthor}").place(
        x=scale(100), y=scale(60), width=scale(300), height=scale(30)
    )

    tkinter.Label(aboutWindows, text="Github").place(
        x=scale(20), y=scale(100), width=scale(60), height=scale(20)
    )
    tkinter.Label(aboutWindows, text="Release").place(
        x=scale(20), y=scale(120), width=scale(60), height=scale(20)
    )
    tkinter.Label(aboutWindows, text="夸克网盘").place(
        x=scale(20), y=scale(140), width=scale(60), height=scale(20)
    )
    tkinter.Label(aboutWindows, text="百度云盘").place(
        x=scale(20), y=scale(160), width=scale(60), height=scale(20)
    )

    label1 = ttk.Label(aboutWindows, text=githubLink, foreground="blue")
    label1.bind("<Button-1>", lambda event: webbrowser.open(githubLink))
    label1.place(x=scale(80), y=scale(100), width=scale(320), height=scale(20))

    label2 = ttk.Label(aboutWindows, text=releaseLink, foreground="blue")
    label2.bind("<Button-1>", lambda event: webbrowser.open(releaseLink))
    label2.place(x=scale(80), y=scale(120), width=scale(320), height=scale(20))

    label3 = ttk.Label(aboutWindows, text=quarkLink, foreground="blue")
    label3.bind("<Button-1>", lambda event: webbrowser.open(quarkLink))
    label3.place(x=scale(80), y=scale(140), width=scale(320), height=scale(20))

    label4 = ttk.Label(
        aboutWindows, text=baiduLink[:30] + "... 提取码: 6666", foreground="blue"
    )
    label4.bind("<Button-1>", lambda event: webbrowser.open(baiduLink))
    label4.place(x=scale(80), y=scale(160), width=scale(320), height=scale(20))


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
        IPv4PortInt = int(IPv4PortVar.get())
        if 0 < IPv4PortInt and IPv4PortInt < 65536:
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
        IPv6PortInt = int(IPv6PortVar.get())
        if 0 < IPv6PortInt and IPv6PortInt < 65536:
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


def copyToClipboard(text: str):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    win32clipboard.CloseClipboard()


def ip_into_int(ip_str: str) -> int:
    return reduce(lambda x, y: (x << 8) + y, map(int, ip_str.split(".")))


# https://blog.mimvp.com/article/32438.html
def is_internal_ip(ip_str: str) -> bool:
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
        userNameEntry.configure(state=tkinter.NORMAL)
        userPasswordEntry.configure(state=tkinter.NORMAL)
        if len(settings.userName) > 0 and len(settings.userPassword) == 0:
            tips: str = "!!! 请设置密码再启动服务 !!!"
            messagebox.showerror("密码异常", tips)
            print(tips)
            return
    else:
        userNameEntry.configure(state=tkinter.DISABLED)
        userPasswordEntry.configure(state=tkinter.DISABLED)

    tipsStr, ftpUrlList = getTipsAndUrlList()

    if len(ftpUrlList) == 0:
        tips: str = "!!! 本机没有检测到网络IP, 请检查网络连接, 或稍后重试 !!!"
        messagebox.showerror("网络异常", tips)
        print(tips)
        return

    settings.save()

    tipsTextWidget.configure(state=tkinter.NORMAL)
    tipsTextWidget.delete("0.0", tkinter.END)
    tipsTextWidget.insert(tkinter.INSERT, tipsStr)
    tipsTextWidget.configure(state=tkinter.DISABLED)

    tipsTextWidgetRightClickMenu.delete(0, len(ftpUrlList))
    for url in ftpUrlList:
        tipsTextWidgetRightClickMenu.add_command(
            label=f"复制 {url}", command=lambda url=url: copyToClipboard(url)
        )

    try:
        if isIPv4Supported:
            serverThreadV4 = threading.Thread(target=serverThreadFunV4)
            serverThreadV4.start()

        if isIPv6Supported:
            serverThreadV6 = threading.Thread(target=serverThreadFunV6)
            serverThreadV6.start()
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
        print("编码: {}\n".format("GBK" if settings.isGBK else "UTF-8"))


def serverThreadFunV4():
    global serverV4
    global isIPv4ThreadRunning
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
        handler.certfile = certFilePath
        handler.keyfile = keyFilePath
        handler.tls_control_required = True
        handler.tls_data_required = True
        print(
            "[FTP IPv4] 已加载 SSL 证书文件, 默认开启 FTPS [TLS/SSL显式加密, TLSv1.3]"
        )
    else:
        handler = FTPHandler

    handler.authorizer = authorizer
    handler.encoding = "gbk" if settings.isGBK else "utf8"
    serverV4 = ThreadedFTPServer(("0.0.0.0", settings.IPv4Port), handler)
    serverV4.max_cons = 4096
    print("[FTP IPv4] 开始运行")
    isIPv4ThreadRunning = True
    serverV4.serve_forever()
    isIPv4ThreadRunning = False
    print("[FTP IPv4] 已关闭")


def serverThreadFunV6():
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

    # handler = FTPHandler
    if os.path.exists(certFilePath) and os.path.exists(keyFilePath):
        handler = TLS_FTPHandler
        handler.certfile = certFilePath
        handler.keyfile = keyFilePath
        handler.tls_control_required = True
        handler.tls_data_required = True
        print(
            "[FTP IPv6] 已加载 SSL 证书文件, 默认开启 FTPS [TLS/SSL显式加密, TLSv1.3]"
        )
    else:
        handler = FTPHandler

    handler.authorizer = authorizer
    handler.encoding = "gbk" if settings.isGBK else "utf8"
    serverV6 = ThreadedFTPServer(("::", settings.IPv6Port), handler)
    serverV6.max_cons = 4096
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

    if isIPv4Supported:
        if isIPv4ThreadRunning:
            print("[FTP IPv4] 正在关闭...")
            serverV4.close_all()  # 注意: 这也会关闭serverV6的所有连接
            serverThreadV4.join()
        print("[FTP IPv4] 线程已关闭")

    if isIPv6Supported:
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
            loggingWidget.configure(state=tkinter.NORMAL)
            loggingWidget.delete(0.0, tkinter.END)
            loggingWidget.configure(state=tkinter.DISABLED)

            logMsgBackup = logMsgBackup[-20:]
            logInfo = ""
            for tmp in logMsgBackup:
                logInfo += tmp

        loggingWidget.configure(state=tkinter.NORMAL)
        loggingWidget.insert(tkinter.END, logInfo)
        loggingWidget.see(tkinter.END)
        loggingWidget.configure(state=tkinter.DISABLED)


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
        ipStr = item[4][0]
        if ":" in ipStr:  # IPv6
            fullUrl = f"ftp://[{ipStr}]" + (
                "" if settings.IPv6Port == 21 else (f":{settings.IPv6Port}")
            )
            IPv6FtpUrlList.append(fullUrl)
            if ipStr[:4] == "fe80" or ipStr[:4] == "fd00":
                IPv6IPstr += f"\n[IPv6 局域网] {fullUrl}"
            elif ipStr[:4] == "240e":
                IPv6IPstr += f"\n[IPv6 电信公网] {fullUrl}"
            elif ipStr[:4] == "2408":
                IPv6IPstr += f"\n[IPv6 联通公网] {fullUrl}"
            elif ipStr[:4] == "2409":
                IPv6IPstr += f"\n[IPv6 移动/铁通网] {fullUrl}"
            else:
                IPv6IPstr += f"\n[IPv6 公网] {fullUrl}"
        elif "." in ipStr:  # IPv4
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

    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)

    mystd = myStdout()  # 实例化重定向类
    logThread = threading.Thread(target=logThreadFun)
    logThread.start()

    strayMenu = (
        pystray.MenuItem("显示", showWindow, default=True),
        pystray.MenuItem("退出", handleExit),
    )
    strayImage = Image.open(BytesIO(base64.b64decode(iconStr)))
    strayIcon = pystray.Icon("icon", strayImage, windowsTitle, strayMenu)
    threading.Thread(target=strayIcon.run, daemon=True).start()

    window = tkinter.Tk()  # 实例化tk对象
    uiFont = font.Font(font=("Consolas"))
    window.geometry(f"{scale(600)}x{scale(500)}")
    window.resizable(False, False)
    window.tk.call("tk", "scaling", ScaleFactor / 75)  # 设置程序缩放

    window.title(windowsTitle)
    iconImage = ImageTk.PhotoImage(data=base64.b64decode(iconStr))
    window.iconphoto(False, iconImage)
    window.protocol("WM_DELETE_WINDOW", hideWindow)

    startButton = ttk.Button(window, text="开启", command=startServer)
    startButton.place(x=scale(10), y=scale(10), width=scale(60), height=scale(25))
    ttk.Button(window, text="关闭", command=closeServer).place(
        x=scale(80), y=scale(10), width=scale(60), height=scale(25)
    )

    ttk.Button(window, text="选择目录", command=pickDirectory).place(
        x=scale(150), y=scale(10), width=scale(70), height=scale(25)
    )

    directoryCombobox = ttk.Combobox(window)
    directoryCombobox.place(
        x=scale(230), y=scale(10), width=scale(220), height=scale(25)
    )

    ttk.Button(window, text="X", command=deleteCurrentComboboxItem, name="asd").place(
        x=scale(450), y=scale(10), width=scale(25), height=scale(25)
    )

    ttk.Button(window, text="帮助", command=showHelp).place(
        x=scale(485), y=scale(10), width=scale(50), height=scale(25)
    )

    ttk.Button(window, text="关于", command=showAbout).place(
        x=scale(540), y=scale(10), width=scale(50), height=scale(25)
    )

    ttk.Label(window, text="用户").place(
        x=scale(10), y=scale(40), width=scale(30), height=scale(25)
    )
    userNameVar = tkinter.StringVar()
    userNameEntry = ttk.Entry(window, textvariable=userNameVar, width=scale(12))
    userNameEntry.place(x=scale(40), y=scale(40), width=scale(150), height=scale(25))

    ttk.Label(window, text="密码").place(
        x=scale(10), y=scale(70), width=scale(30), height=scale(25)
    )
    userPasswordVar = tkinter.StringVar()
    userPasswordEntry = ttk.Entry(
        window, textvariable=userPasswordVar, width=scale(12), show="*"
    )
    userPasswordEntry.place(
        x=scale(40), y=scale(70), width=scale(150), height=scale(25)
    )

    ttk.Label(window, text="IPv4端口").place(
        x=scale(200), y=scale(40), width=scale(60), height=scale(25)
    )
    IPv4PortVar = tkinter.StringVar()
    ttk.Entry(window, textvariable=IPv4PortVar, width=scale(8)).place(
        x=scale(260), y=scale(40), width=scale(50), height=scale(25)
    )

    ttk.Label(window, text="IPv6端口").place(
        x=scale(200), y=scale(70), width=scale(60), height=scale(25)
    )
    IPv6PortVar = tkinter.StringVar()
    ttk.Entry(window, textvariable=IPv6PortVar, width=scale(8)).place(
        x=scale(260), y=scale(70), width=scale(50), height=scale(25)
    )

    isGBKVar = tkinter.BooleanVar()
    ttk.Radiobutton(window, text="UTF-8 编码", variable=isGBKVar, value=False).place(
        x=scale(315), y=scale(40), width=scale(90), height=scale(25)
    )
    ttk.Radiobutton(window, text="GBK 编码", variable=isGBKVar, value=True).place(
        x=scale(315), y=scale(70), width=scale(90), height=scale(25)
    )

    isReadOnlyVar = tkinter.BooleanVar()
    ttk.Radiobutton(window, text="读写", variable=isReadOnlyVar, value=False).place(
        x=scale(400), y=scale(40), width=scale(50), height=scale(25)
    )
    ttk.Radiobutton(window, text="只读", variable=isReadOnlyVar, value=True).place(
        x=scale(400), y=scale(70), width=scale(50), height=scale(25)
    )

    isAutoStartServerVar = tkinter.BooleanVar()
    ttk.Checkbutton(
        window,
        text="下次打开软件后自动\n隐藏窗口并启动服务",
        variable=isAutoStartServerVar,
        onvalue=True,
        offvalue=False,
    ).place(x=scale(460), y=scale(40), width=scale(160), height=scale(50))

    tipsTextWidget = scrolledtext.ScrolledText(
        window, bg="#dddddd", wrap=tkinter.CHAR, font=uiFont
    )
    tipsTextWidget.place(x=scale(10), y=scale(100), width=scale(580), height=scale(150))

    loggingWidget = scrolledtext.ScrolledText(
        window, bg="#dddddd", wrap=tkinter.CHAR, font=uiFont
    )
    loggingWidget.place(x=scale(10), y=scale(260), width=scale(580), height=scale(230))
    loggingWidget.configure(state=tkinter.DISABLED)

    settings = Settings.Settings()
    userList = UserList.UserList()
    if not userList.isEmpty():
        userList.print()
        userNameEntry.configure(state=tkinter.DISABLED)
        userPasswordEntry.configure(state=tkinter.DISABLED)

    directoryCombobox["value"] = tuple(settings.directoryList)
    directoryCombobox.current(0)

    userNameVar.set(settings.userName)
    userPasswordVar.set("******" if len(settings.userPassword) > 0 else "")
    IPv4PortVar.set(str(settings.IPv4Port))
    IPv6PortVar.set(str(settings.IPv6Port))
    isGBKVar.set(settings.isGBK)
    isReadOnlyVar.set(settings.isReadOnly)
    isAutoStartServerVar.set(settings.isAutoStartServer)

    tipsStr, ftpUrlList = getTipsAndUrlList()
    tipsTextWidget.insert(tkinter.INSERT, tipsStr)
    tipsTextWidget.configure(state=tkinter.DISABLED)

    tipsTextWidgetRightClickMenu = tkinter.Menu(window, tearoff=False)
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
