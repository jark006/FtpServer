import time
import tkinter
import threading
import win32clipboard
import win32con
from tkinter import filedialog, ttk, scrolledtext
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer, FTPServer
from pyftpdlib.log import logger
import socket, sys, os, queue
from functools import reduce
import ctypes
import webbrowser

# pip install pyftpdlib qrcode

# 打包 单文件 隐藏终端窗口
# pyinstaller.exe -F -w .\ftpServer.py -i .\ftpServer.ico --add-data ".\ftpServer.ico;."


windowsTitle = 'FTP文件服务器 V1.4    By Github@JARK006'
isSupportdIPV6 = False

logMsg = queue.Queue()
logThreadrunning = True
    
permReadOnly  = 'elr'
permReadWrite = 'elradfmwMT'

isFTP_V4Running = False
isFTP_V6Running = False

class myStdout():	# 重定向类
    def __init__(self):
    	# 将其备份
        self.stdoutbak = sys.stdout		
        self.stderrbak = sys.stderr
        # 重定向
        sys.stdout = self
        sys.stderr = self

    def write(self, info):
        logMsg.put(info)

    def restoreStd(self):
        # 恢复标准输出
        sys.stdout = self.stdoutbak
        sys.stderr = self.stderrbak

def set_clipboard(data):
    win32clipboard.OpenClipboard()
    # win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, data)
    win32clipboard.CloseClipboard()

def ip_into_int(ip):
    # 先把 192.168.31.46 用map分割'.'成数组，然后用reduuce+lambda转成10进制的 3232243502
    # (((((192 * 256) + 168) * 256) + 31) * 256) + 46
    return reduce(lambda x,y:(x<<8)+y,map(int,ip.split('.')))
 
 # https://blog.mimvp.com/article/32438.html
def is_internal_ip(ip_str):
    ip_int = ip_into_int(ip_str)
    net_A = ip_into_int('10.255.255.255') >> 24
    net_B = ip_into_int('172.31.255.255') >> 20
    net_C = ip_into_int('192.168.255.255') >> 16
    net_ISP = ip_into_int('100.127.255.255') >> 22
    net_DHCP = ip_into_int('169.254.255.255') >> 16
    return ip_int >> 24 == net_A or ip_int >>20 == net_B or ip_int >> 16 == net_C or ip_int >> 22 == net_ISP or ip_int >> 16 == net_DHCP

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
    global ipText
    global menu
    global isReadOnly
    global permStr

    userNameStr = userName.get()
    userPasswordStr = userPassword.get()
    if len(userPasswordStr) == 0:
        userPasswordStr = userNameStr

    permStr = permReadOnly if isReadOnly.get() else permReadWrite

    ipInfo = getTips()
    
    ipText.configure(state='normal')
    ipText.delete('0.0', tkinter.END)
    ipText.insert(tkinter.INSERT, ipInfo)
    ipText.configure(state='disable')

    menu.delete(0, len(ipList))
    for ip in ipList:
        menu.add_command(label='复制 '+ip , command=lambda ip=ip:set_clipboard(ip))

    # btn_close()
    try:
        if isFTP_V4Running:
            logger.info ("[FTP ipv4]正在运行")
        else:
            serverThread = threading.Thread(target=startServer)
            serverThread.start()

        if isSupportdIPV6:
            if isFTP_V6Running:
                logger.info ("[FTP ipv6]正在运行")
            else:
                serverThreadV6 = threading.Thread(target=startServerV6)
                serverThreadV6.start()
    except:
        logger.info ("Error: 无法启动线程")

    logger.info ('用户名：'+userNameStr+' 密码：'+userPasswordStr+' 权限：'+('只读'if isReadOnly.get() else '读写'))


def startServer():
    global server
    global isFTP_V4Running
    global v4port
    global userNameStr
    global userPasswordStr
    global permStr

    logger.info ("[FTP ipv4]开启中...")
    dir = ftpDir.get()
    if not os.path.exists(dir):
        logger.info('目录: [ '+dir+' ]不存在！')
        return
    
    authorizer = DummyAuthorizer()

    if len(userNameStr) > 0:
        authorizer.add_user(userNameStr, userPasswordStr, dir, perm = permStr)
    else: 
        authorizer.add_anonymous(dir, perm = permStr)

    handler = FTPHandler
    handler.authorizer = authorizer
    server = ThreadedFTPServer(('0.0.0.0', v4port), handler)
    logger.info("[FTP ipv4]开始运行")
    isFTP_V4Running=True
    server.serve_forever()
    isFTP_V4Running=False
    logger.info('已停止[FTP ipv4]')

def startServerV6():
    global isReadOnly
    global serverV6
    global isFTP_V6Running
    global v6port
    global userNameStr
    global userPasswordStr

    logger.info ("[FTP ipv6]开启中...")
    dir = ftpDir.get()
    if not os.path.exists(dir):
        logger.info('目录: [ '+dir+' ]不存在！')
        return
    authorizer = DummyAuthorizer()

    if len(userNameStr) > 0:
        authorizer.add_user(userNameStr, userPasswordStr, dir, perm = permStr)
    else: 
        authorizer.add_anonymous(dir, perm = permStr)

    handler = FTPHandler
    handler.authorizer = authorizer
    serverV6 = ThreadedFTPServer(('::', v6port), handler)
    logger.info("[FTP ipv6]开始运行")
    isFTP_V6Running=True
    serverV6.serve_forever()
    isFTP_V6Running=False
    logger.info('已停止[FTP ipv6]')

def btn_close():
    global server
    global serverV6
    global serverThread
    global serverThreadV6
    global isFTP_V4Running
    global isFTP_V6Running

    if isFTP_V4Running:
        logger.info('[FTP ipv4]正在停止...')
        server.close_all()
        serverThread.join()
        logger.info('[FTP ipv4]服务线程已退出\n')
    else:
        logger.info('当前没有[FTP ipv4]服务')

    if isFTP_V6Running:
        logger.info('[FTP ipv6]正在停止...')
        serverV6.close_all()
        serverThreadV6.join()
        logger.info('[FTP ipv6]服务线程已退出\n')
    else:
        logger.info('当前没有[FTP ipv6]服务')


def getDir():
    global ftpDir
    dir = filedialog.askdirectory()
    if len(dir) == 0:
        ftpDir.set(os.path.dirname(sys.argv[0]))
    else:
        ftpDir.set(dir)

def openGithub():
    webbrowser.open('https://github.com/jark006/FtpServer')

def handleExit():
    global window
    global logThreadrunning
    global logThread

    logger.info('等待日志线程退出...')
    logThreadrunning = False
    logThread.join()
    logger.info('日志线程已退出.')

    btn_close()

    window.destroy()

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

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
            myConsole.insert('end', logInfo)
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

    ipInfo = '若用户名空白则默认匿名访问(anonymous)，若密码空白则使用用户名作为密码。\n默认UTF-8编码，右键可复制地址'
    ipList = []
    for item in addrs:
        ipStr = item[4][0]
        if ':' in ipStr: # IPV6
            isSupportdIPV6 = True
            fullLink = 'ftp://['+ipStr+']'+('' if v6port == 21 else (':'+str(v6port)))
            ipList.append(fullLink)
            if ipStr[:4] == 'fe80':
                ipInfo += '\n[IPV6   局域网] '+fullLink
            elif ipStr[:4] == '240e':
                ipInfo += '\n[IPV6 电信公网] '+fullLink
            elif ipStr[:4] == '2409':
                ipInfo += '\n[IPV6 联通公网] '+fullLink
            elif ipStr[:4] == '2409':
                ipInfo += '\n[IPV6 移动/铁通网] '+fullLink
            else:
                ipInfo += '\n[IPV6   公网] '+fullLink
            # img = qrcode.make('ftp://['+ipStr+']:30021')
            # ipv6QrcodeImgList.append(img)
        else: # IPV4
            fullLink = 'ftp://'+ipStr+('' if v4port == 21 else (':'+str(v4port)))
            ipList.append(fullLink)
            if is_internal_ip(ipStr):
                if ipStr[:3] == '10.' or ipStr[:3] == '100':
                    ipInfo += '\n[IPV4 运营商局域网] '+fullLink
                else:
                    ipInfo += '\n[IPV4 局域网] '+fullLink
            else:
                ipInfo += '\n[IPV4   公网] '+fullLink

    return ipInfo


def main():
    
    global window
    global isReadOnly
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


    #告诉操作系统使用程序自身的dpi适配
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    ScaleFactor=ctypes.windll.shcore.GetScaleFactorForDevice(0)
    # print("系统缩放比例为:", ScaleFactor)

    def scale(n:int)->int:
        return int(n*ScaleFactor/100)

    mystd = myStdout()	# 实例化重定向类


    logThread = threading.Thread(target=logThreadFun)
    logThread.start()

    window = tkinter.Tk()	# 实例化tk对象
    window.title(windowsTitle)
    window.iconbitmap(resource_path('ftpServer.ico'))
    window.resizable(0,0) #固定窗口
    window.protocol('WM_DELETE_WINDOW', handleExit)

    winWidht = 600
    winHeight = 500
    window.geometry(str(scale(winWidht))+'x'+str(scale(winHeight)))

    ttk.Button(window, text='开启', command=btn_start).place(x=scale(5), y=scale(5), width=scale(60), height=scale(25))
    ttk.Button(window, text='停止', command=btn_close).place(x=scale(65), y=scale(5), width=scale(60), height=scale(25))

    isReadOnly = tkinter.BooleanVar()
    ttk.Radiobutton(window, text = "读写", variable = isReadOnly, value = False).place(x=scale(130), y=scale(5), width=scale(60), height=scale(25))
    ttk.Radiobutton(window, text = "只读", variable = isReadOnly, value = True).place(x=scale(190), y=scale(5), width=scale(60), height=scale(25))
    ttk.Button(window, text='设置目录', command=getDir).place(x=scale(250), y=scale(5), width=scale(70), height=scale(25))

    ftpDir=tkinter.StringVar()
    ttk.Entry(window,textvariable=ftpDir, width=scale(36)).place(x=scale(325), y=scale(5), width=scale(200), height=scale(25))
    ftpDir.set(os.path.dirname(sys.argv[0]))

    ttk.Button(window, text='关于软件', command=openGithub).place(x=scale(530), y=scale(5), width=scale(70), height=scale(25))

    ttk.Label(window, text='用户名').place(x=scale(10), y=scale(40), width=scale(50), height=scale(25))
    userName=tkinter.StringVar()
    ttk.Entry(window,textvariable=userName, width=scale(12)).place(x=scale(60), y=scale(40), width=scale(100), height=scale(25))

    ttk.Label(window, text='密码').place(x=scale(180), y=scale(40), width=scale(40), height=scale(25))
    userPassword=tkinter.StringVar()
    ttk.Entry(window,textvariable=userPassword, width=scale(12)).place(x=scale(220), y=scale(40), width=scale(100), height=scale(25))

    ttk.Label(window, text='IPV4端口').place(x=scale(340), y=scale(40), width=scale(80), height=scale(25))
    ipv4Port=tkinter.StringVar()
    ttk.Entry(window,textvariable=ipv4Port, width=scale(8)).place(x=scale(400), y=scale(40), width=scale(60), height=scale(25))
    ipv4Port.set('21')

    ttk.Label(window, text='IPV6端口').place(x=scale(460), y=scale(40), width=scale(80), height=scale(25))
    ipv6Port=tkinter.StringVar()
    ttk.Entry(window,textvariable=ipv6Port, width=scale(8)).place(x=scale(520), y=scale(40), width=scale(60), height=scale(25))
    ipv6Port.set('30021')

    ipInfo = getTips()
    ipText = tkinter.Text(window, height=len(ipList)+2, fg='black', bg='#e0e0e0', wrap=tkinter.CHAR)
    ipText.insert(tkinter.INSERT, ipInfo)
    ipText.configure(state='disable')
    ipText.place(x=scale(10), y=scale(70), width=scale(580), height=scale(180))

    myConsole = scrolledtext.ScrolledText(window, fg='#dddddd', bg='#282c34', wrap=tkinter.CHAR)
    myConsole.place(x=scale(10), y=scale(260), width=scale(580), height=scale(230))

    menu = tkinter.Menu(window, tearoff=False)
    for ip in ipList:
        menu.add_command(label='复制 '+ip , command=lambda ip=ip:set_clipboard(ip))
    def popup(event):
        menu.post(event.x_root, event.y_root)   # post在指定的位置显示弹出菜单
    ipText.bind('<Button-3>', popup)  # 绑定鼠标右键,执行popup函数

    #设置程序缩放
    window.tk.call('tk', 'scaling', ScaleFactor/75)

    window.mainloop()	# 显示窗体


if __name__ == '__main__':
    main()

