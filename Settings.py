import os, sys, json


class Settings:
    def __init__(self) -> None:
        self.appDirectory = str(os.path.dirname(sys.argv[0])).replace("\\", "/")
        if (
            len(self.appDirectory) > 2
            and self.appDirectory[0].islower()
            and self.appDirectory[1] == ":"
        ):
            self.appDirectory = self.appDirectory[0].upper() + self.appDirectory[1:]

        self.savePath = os.path.join(self.appDirectory, "FtpServer.json")

        self.directoryList: list[str] = [self.appDirectory]
        self.userName: str = "JARK006"
        self.userPassword: str = "123456"
        self.IPv4Port: int = 21
        self.IPv6Port: int = 21
        self.isGBK: bool = True
        self.isReadOnly: bool = True
        self.isAutoStartServer: bool = False

    def load(self):
        if not os.path.exists(self.savePath):
            return

        try:
            with open(self.savePath, "r") as file:
                variables = json.load(file)

            if "rootDirectory" in variables:  # old version: v1.11 and lower
                self.directoryList.clear()
                self.directoryList.append(variables["rootDirectory"])
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
        except:
            print("!!! 设置文件读取异常 !!!")
            return

    def save(self):
        """保存前确保调用 updateSettingVars() 或其他函数进行参数检查"""
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
