import os, sys, json, hashlib


class Settings:
    encryPasswordPrefix = "ENCRY"

    def __init__(self) -> None:
        self.appDirectory = str(os.path.dirname(sys.argv[0])).replace("\\", "/")
        if (
            len(self.appDirectory) > 2
            and self.appDirectory[0].islower()
            and self.appDirectory[1] == ":"
        ):
            self.appDirectory = self.appDirectory[0].upper() + self.appDirectory[1:]

        self.savePath = os.path.join(self.appDirectory, "ftpServer.json")

        self.directoryList: list[str] = [self.appDirectory]
        self.userName: str = "JARK006"
        self.userPassword: str = "123456"
        self.IPv4Port: int = 21
        self.IPv6Port: int = 21
        self.isGBK: bool = True
        self.isReadOnly: bool = True
        self.isAutoStartServer: bool = False
        self.load()

    @staticmethod
    def encry2sha256(input_string: str) -> str:
        if len(input_string) == 0:
            return ""

        salt = "JARK006_FTP_SERVER_SALT"
        sha256_hash = hashlib.sha256()
        sha256_hash.update((input_string + salt).encode("utf-8"))
        return Settings.encryPasswordPrefix + sha256_hash.hexdigest().upper()

    def load(self):
        if not os.path.exists(self.savePath):
            return

        try:
            with open(self.savePath, "r") as file:
                variables = json.load(file)

            if "rootDirectory" in variables:  # old version: v1.11 and lower
                self.directoryList = [variables["rootDirectory"]]
                self.userName = variables["userName"]
                self.userPassword = variables["userPassword"]
                self.IPv4Port = int(variables["ipv4Port"])  # 旧版是小写 "ip"
                self.IPv6Port = int(variables["ipv6Port"])
                self.isGBK = variables["isGBK"] == "1"
                self.isReadOnly = variables["isReadOnly"] == "1"
                self.isAutoStartServer = variables["isAutoStartServer"] == "1"
            else:
                self.directoryList = variables["directoryList"]
                self.userName = variables["userName"]
                self.userPassword = variables["userPassword"]
                self.IPv4Port = variables["IPv4Port"]
                self.IPv6Port = variables["IPv6Port"]
                self.isGBK = variables["isGBK"]
                self.isReadOnly = variables["isReadOnly"]
                self.isAutoStartServer = variables["isAutoStartServer"]

            # 检查变量类型
            if not type(self.directoryList) is list:
                self.directoryList = [self.appDirectory]
                print(f"directoryList 类型错误，已恢复默认：[{self.appDirectory}]")
            if not type(self.userName) is str:
                self.userName = "JARK006"
                print(f"userName 类型错误，已恢复默认：{self.userName}")
            if not type(self.userPassword) is str:
                self.userPassword = "123456"
                print(f"userPassword 类型错误，已恢复默认：{self.userPassword}")
            if not type(self.IPv4Port) is int:
                self.IPv4Port = 21
                print(f"IPv4Port 类型错误，已恢复默认：{self.IPv4Port}")
            if not type(self.IPv6Port) is int:
                self.IPv6Port = 21
                print(f"IPv6Port 类型错误，已恢复默认：{self.IPv6Port}")
            if not type(self.isGBK) is bool:
                self.isGBK = True
                print(f"isGBK 类型错误，已恢复默认：{self.isGBK}")
            if not type(self.isReadOnly) is bool:
                self.isReadOnly = True
                print(f"isReadOnly 类型错误，已恢复默认：{self.isReadOnly}")
            if not type(self.isAutoStartServer) is bool:
                self.isAutoStartServer = False
                print(
                    f"isAutoStartServer 类型错误，已恢复默认：{self.isAutoStartServer}"
                )

            # 旧版(v1.12及以下) 存储的是明文密码
            if len(self.userPassword) > 0 and not self.userPassword.startswith(
                Settings.encryPasswordPrefix
            ):
                self.userPassword = self.encry2sha256(self.userPassword)
                self.save()

        except Exception as e:
            print(f"设置文件读取异常: {self.savePath}\n{e}")
            return

    def save(self):
        """保存前确保调用 updateSettingVars() 或其他函数进行参数检查"""

        while len(self.directoryList) > 20:
            self.directoryList.pop()

        variables: dict[str, any] = {
            "directoryList": self.directoryList,
            "userName": self.userName,
            "userPassword": self.userPassword,
            "IPv4Port": self.IPv4Port,
            "IPv6Port": self.IPv6Port,
            "isGBK": self.isGBK,
            "isReadOnly": self.isReadOnly,
            "isAutoStartServer": self.isAutoStartServer,
        }
        with open(self.savePath, "w") as file:
            json.dump(variables, file)
