import os, sys, re, Settings


class UserNode:
    def __init__(self, userName: str, password: str, perm: str, path: str) -> None:
        self.userName = userName
        self.password = password
        self.perm = perm
        self.path = path


class UserList:
    def __init__(self) -> None:
        self.appDirectory = str(os.path.dirname(sys.argv[0])).replace("\\", "/")
        if (
            len(self.appDirectory) > 2
            and self.appDirectory[0].islower()
            and self.appDirectory[1] == ":"
        ):
            self.appDirectory = self.appDirectory[0].upper() + self.appDirectory[1:]

        self.savePath = os.path.join(self.appDirectory, "FtpServerUserList.csv")

        self.userList: list[UserNode] = list()
        self.userNameSet: set[str] = set()
        self.load()

    def permConvert(self, input: str) -> str:
        """
        Link: https://pyftpdlib.readthedocs.io/en/latest/api.html#pyftpdlib.authorizers.DummyAuthorizer.add_user
        读取权限：
        - "e" = 更改目录 (CWD 命令)
        - "l" = 列出文件 (LIST、NLST、STAT、MLSD、MLST、SIZE、MDTM 命令)
        - "r" = 从服务器检索文件 (RETR 命令)

        写入权限：
        - "a" = 将数据附加到现有文件 (APPE 命令)
        - "d" = 删除文件或目录 (DELE、RMD 命令)
        - "f" = 重命名文件或目录 (RNFR、RNTO 命令)
        - "m" = 创建目录 (MKD 命令)
        - "w" = 将文件存储到服务器 (STOR、STOU 命令)
        - "M" = 更改文件模式 (SITE CHMOD 命令)
        - "T" = 更新文件上次修改时间 (MFMT 命令)
        """

        if input.lower() == "readonly" or input == "只读":
            return "elr"
        elif input.lower() == "readwrite" or input == "读写":
            return "elradfmwMT"
        else:
            charSet = set()
            for c in input:
                if c not in "elradfmwMT":
                    continue
                if c not in charSet:
                    charSet.add(c)
            if len(charSet) == 0:
                return "elr"
            else:
                return "".join(charSet)

    def permTranslate(self, input: str) -> str:
        if input == "elr":
            return "只读"
        elif input == "elradfmwMT":
            return "读写"
        else:
            return input

    def readAllLines(self) -> list[str]:
        for encoding in ['utf-8-sig', 'gbk']:
            try:
                with open(self.savePath, 'r', encoding=encoding) as file:
                    return file.read().splitlines()
            except:
                continue
        print(f"无法使用UTF-8或GBK编码读取文件 {self.savePath}")
        return [""]

    def load(self):
        self.userList.clear()
        self.userNameSet.clear()

        if not os.path.exists(self.savePath):
            return

        try:
            allLines = self.readAllLines()

            for line in allLines:
                if len(line.strip()) == 0:
                    continue
                item = line.split(",")
                if len(item) < 4:
                    print(f"解析错误 [{line}]")
                    continue
                if (
                    len(item[0].strip()) > 0
                    and len(item[1].strip()) > 0
                    and len(item[3].strip()) > 0
                ):
                    if item[0].strip() in self.userNameSet:
                        print(
                            f"发现重复的用户名条目 [{item[0].strip()}], 已跳过此内容 [{line}]"
                        )
                    elif not os.path.exists(item[3].strip()):
                        print(
                            f"该用户名条目 [{item[0].strip()}] 的路径不存在或无访问权限 [{item[3].strip()}] 已跳过此内容 [{line}]"
                        )
                    elif item[0].strip() != "anonymous" and len(item[2].strip()) == 0:
                        print(
                            f"该用户名条目 [{item[0].strip()}] 没有密码(只有匿名用户 anonymous 可以不设密码)，已跳过此内容 [{line}]"
                        )
                    else:
                        self.userNameSet.add(item[0].strip())
                        self.userList.append(
                            UserNode(
                                item[0].strip(),
                                Settings.Settings.encry2sha256(item[1].strip()),
                                self.permConvert(item[2].strip()),
                                item[3].strip().replace('"', ""),
                            )
                        )
                else:
                    print(f"解析错误 [{line}]")
                    continue

        except Exception as e:
            print(f"用户列表文件读取异常: {self.savePath}\n{e}")
            return

    def print(self):
        if len(self.userList) == 0:
            print("用户列表空白")
        else:
            print(f"主页面的用户/密码设置将会忽略，现将使用以下{len(self.userList)}条用户配置:")
            for userItem in self.userList:
                print(
                    f"[{userItem.userName}] [******] [{self.permTranslate(userItem.perm)}] [{userItem.path}]"
                )
            print('')

    def isEmpty(self) -> bool:
        return len(self.userList) == 0
