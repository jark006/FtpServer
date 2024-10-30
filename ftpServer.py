import socket, sys, os, queue, time, base64, threading, ctypes, webbrowser, pystray

import Settings
import win32clipboard
import win32con
import tkinter

from tkinter import ttk, scrolledtext, filedialog
from mypyftpdlib.authorizers import DummyAuthorizer
from mypyftpdlib.handlers import FTPHandler
from mypyftpdlib.servers import ThreadedFTPServer
from PIL import ImageTk, Image
from io import BytesIO

# pip install Pillow pypiwin32 pyinstaller nuitka pystray

# 打包 单文件 隐藏终端窗口
# pyinstaller.exe -F -w .\ftpServer.py -i .\ftpServer.ico --version-file .\file_version_info.txt
# nuitka --standalone --onefile --enable-plugin=tk-inter --windows-disable-console .\ftpServer.py --windows-icon-from-ico=.\ftpServer.ico
"""
import base64
with open(r"ico64x64.ico", "rb") as f:
    iconStr = base64.b64encode(f.read())
    print(iconStr)
"""
iconStr = b"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"


appName = "FTP Server"
appLabel = "FTP文件服务器"
appVersion = "v1.13"
appAuthor = "Github@JARK006"
githubLink = "https://github.com/jark006/FtpServer"
windowsTitle = f"{appLabel} {appVersion} By {appAuthor}"
tipsTitle = "若用户名空白则默认匿名访问(anonymous)。若中文乱码则需更换编码方式，再重启服务。请设置完后再开启服务。以下为本机所有IP地址，右键可复制。\n"

logMsg = queue.Queue()
logThreadrunning: bool = True

permReadOnly: str = "elr"
permReadWrite: str = "elradfmwMT"

isIPv4Supported: bool = False
isIPv6Supported: bool = False
isIPv4ThreadRunning: bool = False
isIPv6ThreadRunning: bool = False

settings = Settings.Settings()


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
    settings.userPassword = userPasswordVar.get()
    settings.isGBK = isGBKVar.get()
    settings.isReadOnly = isReadOnlyVar.get()
    settings.isAutoStartServer = isAutoStartServerVar.get()

    try:
        IPv4PortInt = int(IPv4PortVar.get())
        if 0 < IPv4PortInt and IPv4PortInt < 65536:
            settings.IPv4Port = IPv4PortInt
        else:
            raise
    except:
        print(
            f"\n\n!!! 当前 IPv4 设置端口：{IPv4PortVar.get()} 错误，正常范围: 1 ~ 65535，已重设为: 21\n\n"
        )
        settings.IPv4Port = 21
        IPv4PortVar.set("21")

    try:
        IPv6PortInt = int(IPv6PortVar.get())
        if 0 < IPv6PortInt and IPv6PortInt < 65536:
            settings.IPv6Port = IPv6PortInt
        else:
            raise
    except:
        print(
            f"\n\n!!! 当前 IPv6 设置端口：{IPv6PortVar.get()} 错误，正常范围: 1 ~ 65535，已重设为: 21\n\n"
        )
        settings.IPv6Port = 21
        IPv6PortVar.set("21")


class myStdout:  # 重定向输出
    def __init__(self):
        sys.stdout = self
        sys.stderr = self

    def write(self, info):
        logMsg.put(info)


def set_clipboard(data):
    win32clipboard.OpenClipboard()
    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, data)
    win32clipboard.CloseClipboard()


def ip_into_int(ip_str):
    parts = ip_str.split(".")
    ip_int = (
        (int(parts[0]) << 24)
        + (int(parts[1]) << 16)
        + (int(parts[2]) << 8)
        + int(parts[3])
    )
    return ip_int


# https://blog.mimvp.com/article/32438.html
def is_internal_ip(ip_str):
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
    global serverThreadV4
    global serverThreadV6
    global isIPv4Supported
    global isIPv6Supported
    global isIPv4ThreadRunning
    global isIPv6ThreadRunning
    global tipsTextWidget
    global tipsTextWidgetRightClickMenu

    if isIPv4ThreadRunning:
        print("[FTP IPv4]正在运行")
        return
    if isIPv6ThreadRunning:
        print("[FTP IPv6]正在运行")
        return

    updateSettingVars()

    if not os.path.exists(settings.directoryList[0]):
        print(
            f"路径: [ {settings.directoryList[0]} ]异常！请检查路径是否正确或者有没有读取权限。"
        )
        return

    if len(settings.userName) > 0 and len(settings.userPassword) == 0:
        print("\n\n!!! 请设置密码再启动服务 !!!")
        return

    tipsStr, ftpUrlList = getTipsAndUrlList()

    if len(ftpUrlList) == 0:
        print("\n\n!!! 本机没有检测到网络IP，请检查网络连接，或稍后重试 !!!")
        return

    settings.save()

    tipsTextWidget.configure(state="normal")
    tipsTextWidget.delete("0.0", tkinter.END)
    tipsTextWidget.insert(tkinter.INSERT, tipsStr)
    tipsTextWidget.configure(state="disable")

    tipsTextWidgetRightClickMenu.delete(0, len(ftpUrlList))
    for url in ftpUrlList:
        tipsTextWidgetRightClickMenu.add_command(
            label=f"复制 {url}", command=lambda url=url: set_clipboard(url)
        )

    try:
        if isIPv4Supported:
            serverThreadV4 = threading.Thread(target=serverThreadFunV4)
            serverThreadV4.start()

        if isIPv6Supported:
            serverThreadV6 = threading.Thread(target=serverThreadFunV6)
            serverThreadV6.start()
    except Exception as e:
        print("!!! 发生异常，无法启动线程: ", e)

    print(
        "\n用户名: {}\n密码: {}\n权限: {}\n编码: {}\n目录: {}\n".format(
            (
                settings.userName
                if len(settings.userName) > 0
                else "匿名访问(anonymous)"
            ),
            settings.userPassword,
            ("只读" if settings.isReadOnly else "读写"),
            ("GBK" if settings.isGBK else "UTF-8"),
            settings.directoryList[0],
        )
    )


def serverThreadFunV4():
    global serverV4
    global isIPv4ThreadRunning

    print("[FTP IPv4]开启中...")
    authorizer = DummyAuthorizer()

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

    handler = FTPHandler
    handler.authorizer = authorizer
    handler.encoding = "gbk" if settings.isGBK else "utf8"
    serverV4 = ThreadedFTPServer(("0.0.0.0", settings.IPv4Port), handler)
    print("[FTP IPv4]开始运行")
    isIPv4ThreadRunning = True
    serverV4.serve_forever()
    isIPv4ThreadRunning = False
    print("已停止[FTP IPv4]")


def serverThreadFunV6():
    global serverV6
    global isIPv6ThreadRunning

    print("[FTP IPv6]开启中...")
    authorizer = DummyAuthorizer()

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

    handler = FTPHandler
    handler.authorizer = authorizer
    handler.encoding = "gbk" if settings.isGBK else "utf8"
    serverV6 = ThreadedFTPServer(("::", settings.IPv6Port), handler)
    print("[FTP IPv6]开始运行")
    isIPv6ThreadRunning = True
    serverV6.serve_forever()
    isIPv6ThreadRunning = False
    print("已停止[FTP IPv6]")


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
            print("[FTP IPv4]正在停止...")
            serverV4.close_all()  # 注意：这也会关闭serverV6的所有连接
            serverThreadV4.join()
        print("[FTP IPv4] 线程已停止")

    if isIPv6Supported:
        if isIPv6ThreadRunning:
            print("[FTP IPv6]正在停止...")
            serverV6.close_all()
            serverThreadV6.join()
        print("[FTP IPv6] 线程已停止")


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
            while len(settings.directoryList) > 20:
                settings.directoryList.pop()

        directoryCombobox["value"] = tuple(settings.directoryList)
        directoryCombobox.current(0)
    else:
        print(f"路径不存在或无访问权限：{directory}")


def openGithub():
    webbrowser.open(githubLink)


def show_window():
    global window
    window.deiconify()


def hide_window():
    global window
    window.withdraw()


def handleExit(icon: pystray._base.Icon):
    global window
    global logThreadrunning
    global logThread

    icon.stop()
    print("等待日志线程退出...")
    logThreadrunning = False
    logThread.join()

    updateSettingVars()
    settings.save()

    closeServer()
    window.destroy()
    exit(0)


def logThreadFun():
    global logThreadrunning
    global loggingWidget
    cnt: int = 0
    while logThreadrunning:
        if logMsg.empty():
            time.sleep(0.1)
            continue

        cnt += 1
        if cnt > 100:
            cnt = 0
            loggingWidget.configure(state="normal")
            loggingWidget.delete(0.0, tkinter.END)
            loggingWidget.configure(state="disable")

        logInfo = ""
        while not logMsg.empty():
            logInfo += logMsg.get()

        loggingWidget.configure(state="normal")
        loggingWidget.insert("end", logInfo)
        loggingWidget.see(tkinter.END)
        loggingWidget.configure(state="disable")


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

    global window
    global loggingWidget
    global logThread
    global tipsTextWidget
    global tipsTextWidgetRightClickMenu
    global directoryCombobox

    global userNameVar
    global userPasswordVar
    global IPv4PortVar
    global IPv6PortVar
    global isReadOnlyVar
    global isGBKVar
    global isAutoStartServerVar

    # 告诉操作系统使用程序自身的dpi适配
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)

    def scale(n: int) -> int:
        return int(n * ScaleFactor / 100)

    mystd = myStdout()  # 实例化重定向类

    settings.load()

    strayMenu = (
        pystray.MenuItem("显示", show_window, default=True),
        pystray.MenuItem("退出", handleExit),
    )
    strayImage = Image.open(BytesIO(base64.b64decode(iconStr)))
    strayIcon = pystray.Icon("icon", strayImage, "FTP服务器", strayMenu)

    logThread = threading.Thread(target=logThreadFun)
    logThread.start()

    window = tkinter.Tk()  # 实例化tk对象
    window.title(windowsTitle)
    icon_img = ImageTk.PhotoImage(data=base64.b64decode(iconStr))
    window.tk.call("wm", "iconphoto", window._w, icon_img)

    window.resizable(0, 0)  # 固定窗口
    window.protocol("WM_DELETE_WINDOW", hide_window)

    winWidht = 600
    winHeight = 500
    window.geometry(f"{scale(winWidht)}x{scale(winHeight)}")

    startButton = ttk.Button(window, text="开启", command=startServer)
    startButton.place(x=scale(10), y=scale(10), width=scale(60), height=scale(25))
    ttk.Button(window, text="停止", command=closeServer).place(
        x=scale(80), y=scale(10), width=scale(60), height=scale(25)
    )

    ttk.Button(window, text="选择目录", command=pickDirectory).place(
        x=scale(150), y=scale(10), width=scale(70), height=scale(25)
    )

    directoryCombobox = ttk.Combobox(window, state="readonly")
    directoryCombobox.place(
        x=scale(230), y=scale(10), width=scale(280), height=scale(25)
    )

    ttk.Button(window, text="关于/更新", command=openGithub).place(
        x=scale(520), y=scale(10), width=scale(70), height=scale(25)
    )

    ttk.Label(window, text="用户名").place(
        x=scale(10), y=scale(40), width=scale(50), height=scale(25)
    )
    userNameVar = tkinter.StringVar()
    ttk.Entry(window, textvariable=userNameVar, width=scale(12)).place(
        x=scale(60), y=scale(40), width=scale(100), height=scale(25)
    )

    ttk.Label(window, text="密码").place(
        x=scale(10), y=scale(70), width=scale(40), height=scale(25)
    )
    userPasswordVar = tkinter.StringVar()
    ttk.Entry(window, textvariable=userPasswordVar, width=scale(12)).place(
        x=scale(60), y=scale(70), width=scale(100), height=scale(25)
    )

    ttk.Label(window, text="IPv4端口").place(
        x=scale(180), y=scale(40), width=scale(80), height=scale(25)
    )
    IPv4PortVar = tkinter.StringVar()
    ttk.Entry(window, textvariable=IPv4PortVar, width=scale(8)).place(
        x=scale(240), y=scale(40), width=scale(60), height=scale(25)
    )

    ttk.Label(window, text="IPv6端口").place(
        x=scale(180), y=scale(70), width=scale(80), height=scale(25)
    )
    IPv6PortVar = tkinter.StringVar()
    ttk.Entry(window, textvariable=IPv6PortVar, width=scale(8)).place(
        x=scale(240), y=scale(70), width=scale(60), height=scale(25)
    )

    isGBKVar = tkinter.BooleanVar()
    ttk.Radiobutton(window, text="UTF-8 编码", variable=isGBKVar, value=False).place(
        x=scale(310), y=scale(40), width=scale(100), height=scale(25)
    )
    ttk.Radiobutton(window, text="GBK 编码", variable=isGBKVar, value=True).place(
        x=scale(310), y=scale(70), width=scale(100), height=scale(25)
    )

    isReadOnlyVar = tkinter.BooleanVar()
    ttk.Radiobutton(window, text="读写", variable=isReadOnlyVar, value=False).place(
        x=scale(400), y=scale(40), width=scale(100), height=scale(25)
    )
    ttk.Radiobutton(window, text="只读", variable=isReadOnlyVar, value=True).place(
        x=scale(400), y=scale(70), width=scale(100), height=scale(25)
    )

    isAutoStartServerVar = tkinter.BooleanVar()
    ttk.Checkbutton(
        window,
        text="下次打开软件后自动\n隐藏窗口并启动服务",
        variable=isAutoStartServerVar,
        onvalue=True,
        offvalue=False,
    ).place(x=scale(460), y=scale(40), width=scale(160), height=scale(50))

    tipsStr, ftpUrlList = getTipsAndUrlList()

    tipsTextWidget = scrolledtext.ScrolledText(window, bg="#dddddd", wrap=tkinter.CHAR)
    tipsTextWidget.insert(tkinter.INSERT, tipsStr)
    tipsTextWidget.configure(state="disable")
    tipsTextWidget.place(x=scale(10), y=scale(100), width=scale(580), height=scale(150))

    tipsTextWidgetRightClickMenu = tkinter.Menu(window, tearoff=False)
    for url in ftpUrlList:
        tipsTextWidgetRightClickMenu.add_command(
            label=f"复制 {url}", command=lambda url=url: set_clipboard(url)
        )

    def popup(event: tkinter.Event):
        tipsTextWidgetRightClickMenu.post(
            event.x_root, event.y_root
        )  # post在指定的位置显示弹出菜单

    tipsTextWidget.bind("<Button-3>", popup)  # 绑定鼠标右键,执行popup函数

    loggingWidget = scrolledtext.ScrolledText(window, bg="#dddddd", wrap=tkinter.CHAR)
    loggingWidget.place(x=scale(10), y=scale(260), width=scale(580), height=scale(230))
    loggingWidget.configure(state="disable")

    # 设置程序缩放
    window.tk.call("tk", "scaling", ScaleFactor / 75)

    directoryCombobox["value"] = tuple(settings.directoryList)
    directoryCombobox.current(0)

    userNameVar.set(settings.userName)
    userPasswordVar.set(settings.userPassword)
    IPv4PortVar.set(str(settings.IPv4Port))
    IPv6PortVar.set(str(settings.IPv6Port))
    isGBKVar.set(settings.isGBK)
    isReadOnlyVar.set(settings.isReadOnly)
    isAutoStartServerVar.set(settings.isAutoStartServer)

    threading.Thread(target=strayIcon.run, daemon=True).start()

    if settings.isAutoStartServer:
        startButton.invoke()
        window.withdraw()

    window.mainloop()


if __name__ == "__main__":
    main()
