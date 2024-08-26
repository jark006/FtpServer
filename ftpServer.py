import socket, sys, os, queue, time, base64, threading, ctypes, webbrowser, json

import tkinter
from tkinter import ttk, scrolledtext, filedialog

from mypyftpdlib.authorizers import DummyAuthorizer
from mypyftpdlib.handlers import FTPHandler
from mypyftpdlib.servers import ThreadedFTPServer
from mypyftpdlib.log import logger

from PIL import ImageTk

import win32clipboard
import win32con

# pip install Pillow pypiwin32 pyinstaller

# 打包 单文件 隐藏终端窗口
# pyinstaller.exe -F -w .\ftpServer.py -i .\ftpServer.ico
"""
import base64
with open(r"ico64x64.ico", "rb") as f:
    iconStr = base64.b64encode(f.read())
    print(iconStr)
"""
iconStr = b"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"


appName = "FTP Server"
appLabel = "FTP文件服务器"
appVersion = "v1.8"
appAuthor = "Github@JARK006"
windowsTitle = appLabel + " " + appVersion + " By " + appAuthor

logMsg = queue.Queue()
logThreadrunning = True

permReadOnly = "elr"
permReadWrite = "elradfmwMT"

isGBKEncode = False
isSupportdIPV6 = False
isFTP_V4Running = False
isFTP_V6Running = False

settingParameters: dict[str, str] = {
    "rootDir": "",
    "userName": "",
    "userPassword": "",
    "ipv4Port": "21",
    "ipv6Port": "30021",
    "isGBK": "0",
    "isReadOnly": "0",
}


def load_variables(filename="FtpServer.json"):
    global settingParameters

    file_path = os.path.join(os.path.dirname(sys.argv[0]), filename)

    if not os.path.exists(file_path):
        return

    with open(file_path, "r") as file:
        variables = json.load(file)

    for key, value in variables.items():
        if key in settingParameters:
            settingParameters[key] = value


def save_variables(filename="FtpServer.json"):
    global settingParameters

    with open(os.path.join(os.path.dirname(sys.argv[0]), filename), "w") as file:
        json.dump(settingParameters, file)


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
    net_A = ip_into_int("10.255.255.255") >> 24
    net_B = ip_into_int("172.31.255.255") >> 20
    net_C = ip_into_int("192.168.255.255") >> 16
    net_ISP = ip_into_int("100.127.255.255") >> 22
    net_DHCP = ip_into_int("169.254.255.255") >> 16
    return (
        ip_int >> 24 == net_A
        or ip_int >> 20 == net_B
        or ip_int >> 16 == net_C
        or ip_int >> 22 == net_ISP
        or ip_int >> 16 == net_DHCP
    )


def btn_start():
    global serverThread
    global serverThreadV6
    global isSupportdIPV6
    global isFTP_V4Running
    global isFTP_V6Running
    global userName
    global userPassword
    global userNameStr
    global userPasswordStr
    global ipv4Port
    global ipv6Port
    global ipText
    global menu
    global isReadOnly
    global isGBK_Encoding

    userNameStr = userName.get()
    userPasswordStr = userPassword.get()
    if len(userPasswordStr) == 0:
        userPasswordStr = userNameStr

    settingParameters["rootDir"] = ftpDir.get()
    settingParameters["userName"] = userNameStr
    settingParameters["userPassword"] = userPasswordStr
    settingParameters["ipv4Port"] = ipv4Port.get()
    settingParameters["ipv6Port"] = ipv6Port.get()
    settingParameters["isGBK"] = "1" if isGBK_Encoding.get() else "0"
    settingParameters["isReadOnly"] = "1" if isReadOnly.get() else "0"
    save_variables()

    ipInfo = getTips()

    ipText.configure(state="normal")
    ipText.delete("0.0", tkinter.END)
    ipText.insert(tkinter.INSERT, ipInfo)
    ipText.configure(state="disable")

    menu.delete(0, len(ipList))
    for ip in ipList:
        menu.add_command(label="复制 " + ip, command=lambda ip=ip: set_clipboard(ip))

    # btn_close()
    try:
        if isFTP_V4Running:
            logger.info("[FTP ipv4]正在运行")
        else:
            serverThread = threading.Thread(target=startServer)
            serverThread.start()

        if isSupportdIPV6:
            if isFTP_V6Running:
                logger.info("[FTP ipv6]正在运行")
            else:
                serverThreadV6 = threading.Thread(target=startServerV6)
                serverThreadV6.start()
    except:
        print("Error: 无法启动线程")

    print(
        "\n用户名: {}\n密码: {}\n权限: {}\n编码: {}\n".format(
            userNameStr if len(userNameStr) > 0 else "匿名访问(anonymous)",
            userPasswordStr,
            ("只读" if isReadOnly.get() else "读写"),
            ("GBK" if isGBK_Encoding.get() else "UTF-8"),
        )
    )


def startServer():
    global server
    global isFTP_V4Running
    global v4port
    global userNameStr
    global userPasswordStr
    global isReadOnly
    global isGBK_Encoding

    logger.info("[FTP ipv4]开启中...")
    dir = ftpDir.get()
    if not os.path.exists(dir):
        logger.info("目录: [ " + dir + " ]不存在！")
        return

    authorizer = DummyAuthorizer()
    permStr = permReadOnly if isReadOnly.get() else permReadWrite
    encodingStr = "gbk" if isGBK_Encoding.get() else "utf8"

    if len(userNameStr) > 0:
        authorizer.add_user(userNameStr, userPasswordStr, dir, perm=permStr)
    else:
        authorizer.add_anonymous(dir, perm=permStr)

    handler = FTPHandler
    handler.authorizer = authorizer
    handler.encoding = encodingStr
    server = ThreadedFTPServer(("0.0.0.0", v4port), handler)
    logger.info("[FTP ipv4]开始运行")
    isFTP_V4Running = True
    server.serve_forever()
    isFTP_V4Running = False
    logger.info("已停止[FTP ipv4]")


def startServerV6():
    global isReadOnly
    global isGBK_Encoding
    global serverV6
    global isFTP_V6Running
    global v6port
    global userNameStr
    global userPasswordStr

    logger.info("[FTP ipv6]开启中...")
    dir = ftpDir.get()
    if not os.path.exists(dir):
        logger.info("目录: [ " + dir + " ]不存在！")
        return

    authorizer = DummyAuthorizer()
    permStr = permReadOnly if isReadOnly.get() else permReadWrite
    encodingStr = "gbk" if isGBK_Encoding.get() else "utf8"

    if len(userNameStr) > 0:
        authorizer.add_user(userNameStr, userPasswordStr, dir, perm=permStr)
    else:
        authorizer.add_anonymous(dir, perm=permStr)

    handler = FTPHandler
    handler.authorizer = authorizer
    handler.encoding = encodingStr
    serverV6 = ThreadedFTPServer(("::", v6port), handler)
    logger.info("[FTP ipv6]开始运行")
    isFTP_V6Running = True
    serverV6.serve_forever()
    isFTP_V6Running = False
    logger.info("已停止[FTP ipv6]")


def btn_close():
    global server
    global serverV6
    global serverThread
    global serverThreadV6
    global isFTP_V4Running
    global isFTP_V6Running

    if isFTP_V4Running:
        logger.info("[FTP ipv4]正在停止...")
        server.close_all()
        serverThread.join()
        logger.info("[FTP ipv4]服务线程已退出\n")
    else:
        logger.info("当前没有[FTP ipv4]服务")

    if isFTP_V6Running:
        logger.info("[FTP ipv6]正在停止...")
        serverV6.close_all()
        serverThreadV6.join()
        logger.info("[FTP ipv6]服务线程已退出\n")
    else:
        logger.info("当前没有[FTP ipv6]服务")


def getDir():
    global ftpDir
    dir = filedialog.askdirectory()
    if len(dir) == 0:
        ftpDir.set(os.path.dirname(sys.argv[0]))
    else:
        ftpDir.set(dir)


def openGithub():
    webbrowser.open("https://github.com/jark006/FtpServer")


def handleExit():
    global window
    global logThreadrunning
    global logThread

    logger.info("等待日志线程退出...")
    logThreadrunning = False
    logThread.join()
    logger.info("日志线程已退出.")

    btn_close()

    window.destroy()


def logThreadFun():
    global logThreadrunning
    global myConsole
    cnt = 0
    while logThreadrunning:
        while not logMsg.empty():
            cnt += 1
            if cnt > 1000:
                cnt = 0
                myConsole.delete(0.0, tkinter.END)

            logInfo = logMsg.get()
            myConsole.insert("end", logInfo)
            myConsole.see(tkinter.END)
        time.sleep(0.1)


def getTips():
    global ipList
    global isSupportdIPV6
    global ipv4Port
    global ipv6Port
    global v4port
    global v6port

    addrs = socket.getaddrinfo(socket.gethostname(), None)

    v4port = int(ipv4Port.get())
    if v4port <= 0 or v4port >= 65535:
        v4port = 21
    v6port = int(ipv6Port.get())
    if v6port <= 0 or v6port >= 65535:
        v6port = 30021

    ipv4IPstr = ""
    ipv6IPstr = ""
    ipv4List = []
    ipv6List = []
    for item in addrs:
        ipStr = item[4][0]
        if ":" in ipStr:  # IPV6
            isSupportdIPV6 = True
            fullLink = (
                "ftp://[" + ipStr + "]" + ("" if v6port == 21 else (":" + str(v6port)))
            )
            ipv6List.append(fullLink)
            if ipStr[:4] == "fe80":
                ipv6IPstr += "\n[IPV6   局域网] " + fullLink
            elif ipStr[:4] == "240e":
                ipv6IPstr += "\n[IPV6 电信公网] " + fullLink
            elif ipStr[:4] == "2409":
                ipv6IPstr += "\n[IPV6 联通公网] " + fullLink
            elif ipStr[:4] == "2409":
                ipv6IPstr += "\n[IPV6 移动/铁通网] " + fullLink
            else:
                ipv6IPstr += "\n[IPV6   公网] " + fullLink
            # img = qrcode.make("ftp://["+ipStr+"]:30021")
            # ipv6QrcodeImgList.append(img)
        else:  # IPV4
            fullLink = "ftp://" + ipStr + ("" if v4port == 21 else (":" + str(v4port)))
            ipv4List.append(fullLink)
            if is_internal_ip(ipStr):
                if ipStr[:3] == "10." or ipStr[:3] == "100":
                    ipv4IPstr += "\n[IPV4 运营商局域网] " + fullLink
                else:
                    ipv4IPstr += "\n[IPV4 局域网] " + fullLink
            else:
                ipv4IPstr += "\n[IPV4   公网] " + fullLink

    ipList = ipv4List + ipv6List
    ipInfo = "若用户名空白则默认匿名访问(anonymous)，若密码空白则使用用户名作为密码。若中文乱码则需更换编码方式，再重启服务。请设置完后再开启服务。服务正常开启才会保存设置。以下为本机所有IP地址，右键可复制。\n"
    return ipInfo + ipv4IPstr + ipv6IPstr


def main():

    global window
    global isReadOnly
    global isGBK_Encoding
    global ftpDir
    global myConsole
    global isSupportdIPV6
    global logThread
    global userName
    global userPassword
    global ipv4Port
    global ipv6Port
    global ipList
    global ipText
    global menu

    # 告诉操作系统使用程序自身的dpi适配
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    # print("系统缩放比例为:", ScaleFactor)

    def scale(n: int) -> int:
        return int(n * ScaleFactor / 100)

    mystd = myStdout()  # 实例化重定向类

    logThread = threading.Thread(target=logThreadFun)
    logThread.start()

    window = tkinter.Tk()  # 实例化tk对象
    window.title(windowsTitle)
    icon_img = ImageTk.PhotoImage(data=base64.b64decode(iconStr))
    window.tk.call("wm", "iconphoto", window._w, icon_img)

    window.resizable(0, 0)  # 固定窗口
    window.protocol("WM_DELETE_WINDOW", handleExit)

    winWidht = 600
    winHeight = 500
    window.geometry(str(scale(winWidht)) + "x" + str(scale(winHeight)))

    ttk.Button(window, text="开启", command=btn_start).place(
        x=scale(10), y=scale(10), width=scale(60), height=scale(25)
    )
    ttk.Button(window, text="停止", command=btn_close).place(
        x=scale(80), y=scale(10), width=scale(60), height=scale(25)
    )

    ttk.Button(window, text="设置目录", command=getDir).place(
        x=scale(150), y=scale(10), width=scale(70), height=scale(25)
    )

    ftpDir = tkinter.StringVar()
    ttk.Entry(window, textvariable=ftpDir, width=scale(36)).place(
        x=scale(230), y=scale(10), width=scale(280), height=scale(25)
    )

    ttk.Button(window, text="关于/更新", command=openGithub).place(
        x=scale(520), y=scale(10), width=scale(70), height=scale(25)
    )

    ttk.Label(window, text="用户名").place(
        x=scale(10), y=scale(40), width=scale(50), height=scale(25)
    )
    userName = tkinter.StringVar()
    ttk.Entry(window, textvariable=userName, width=scale(12)).place(
        x=scale(60), y=scale(40), width=scale(100), height=scale(25)
    )

    ttk.Label(window, text="密码").place(
        x=scale(10), y=scale(70), width=scale(40), height=scale(25)
    )
    userPassword = tkinter.StringVar()
    ttk.Entry(window, textvariable=userPassword, width=scale(12)).place(
        x=scale(60), y=scale(70), width=scale(100), height=scale(25)
    )

    ttk.Label(window, text="IPV4端口").place(
        x=scale(180), y=scale(40), width=scale(80), height=scale(25)
    )
    ipv4Port = tkinter.StringVar()
    ttk.Entry(window, textvariable=ipv4Port, width=scale(8)).place(
        x=scale(240), y=scale(40), width=scale(60), height=scale(25)
    )
    ipv4Port.set("21")

    ttk.Label(window, text="IPV6端口").place(
        x=scale(180), y=scale(70), width=scale(80), height=scale(25)
    )
    ipv6Port = tkinter.StringVar()
    ttk.Entry(window, textvariable=ipv6Port, width=scale(8)).place(
        x=scale(240), y=scale(70), width=scale(60), height=scale(25)
    )
    ipv6Port.set("30021")

    isGBK_Encoding = tkinter.BooleanVar()
    ttk.Radiobutton(
        window, text="UTF-8 编码", variable=isGBK_Encoding, value=False
    ).place(x=scale(320), y=scale(40), width=scale(100), height=scale(25))
    ttk.Radiobutton(window, text="GBK 编码", variable=isGBK_Encoding, value=True).place(
        x=scale(320), y=scale(70), width=scale(100), height=scale(25)
    )

    isReadOnly = tkinter.BooleanVar()
    ttk.Radiobutton(window, text="读写", variable=isReadOnly, value=False).place(
        x=scale(420), y=scale(40), width=scale(100), height=scale(25)
    )
    ttk.Radiobutton(window, text="只读", variable=isReadOnly, value=True).place(
        x=scale(420), y=scale(70), width=scale(100), height=scale(25)
    )

    ipInfo = getTips()
    ipText = scrolledtext.ScrolledText(
        window, fg="black", bg="#e0e0e0", wrap=tkinter.CHAR
    )
    ipText.insert(tkinter.INSERT, ipInfo)
    ipText.configure(state="disable")
    ipText.place(x=scale(10), y=scale(100), width=scale(580), height=scale(150))

    myConsole = scrolledtext.ScrolledText(
        window, fg="#dddddd", bg="#282c34", wrap=tkinter.CHAR
    )
    myConsole.place(x=scale(10), y=scale(260), width=scale(580), height=scale(230))

    menu = tkinter.Menu(window, tearoff=False)
    for ip in ipList:
        menu.add_command(label="复制 " + ip, command=lambda ip=ip: set_clipboard(ip))

    def popup(event):
        menu.post(event.x_root, event.y_root)  # post在指定的位置显示弹出菜单

    ipText.bind("<Button-3>", popup)  # 绑定鼠标右键,执行popup函数

    # 设置程序缩放
    window.tk.call("tk", "scaling", ScaleFactor / 75)

    load_variables()

    if os.path.exists(settingParameters["rootDir"]):
        ftpDir.set(settingParameters["rootDir"])
    else:
        ftpDir.set(os.path.dirname(sys.argv[0]))

    if len(settingParameters["userName"]) > 0:
        userName.set(settingParameters["userName"])
    if len(settingParameters["userPassword"]) > 0:
        userPassword.set(settingParameters["userPassword"])
    if len(settingParameters["ipv4Port"]) > 0:
        ipv4Port.set(settingParameters["ipv4Port"])
    if len(settingParameters["ipv6Port"]) > 0:
        ipv6Port.set(settingParameters["ipv6Port"])

    isGBK_Encoding.set(True if settingParameters["isGBK"] == "1" else False)
    isReadOnly.set(True if settingParameters["isReadOnly"] == "1" else False)

    window.mainloop()  # 显示窗体


if __name__ == "__main__":
    main()
