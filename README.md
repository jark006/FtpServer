# 🖥️ FTP文件服务器

![Version](https://img.shields.io/github/v/release/jark006/ftpServer) ![Stars](https://img.shields.io/github/stars/jark006/ftpServer) ![License](https://img.shields.io/github/license/jark006/ftpServer) ![Issues](https://img.shields.io/github/issues/jark006/ftpServer)

一键开启FTP文件服务器，方便其他设备通过网络传输、管理文件，支持IPv4，IPv6。

---

## 🔐 FTPS 配置

在 `Linux` 或 `MinGW64` 终端使用 `openssl` (命令如下，需填入一些简单信息: 地区/名字/Email等)生成SSL证书文件(ftpServer.key和ftpServer.crt), `不要重命名`文件为其他名称。

```sh
openssl req -x509 -newkey rsa:2048 -keyout ftpServer.key -out ftpServer.crt -nodes -days 36500
```

直接将 `ftpServer.key` 和 `ftpServer.crt` 放到程序所在目录, 开启服务时若存在这两个文件, 则启用加密传输 `FTPS [TLS/SSL显式加密, TLSv1.3]`。

Windows文件管理器对 `显式FTPS` 支持不佳, 推荐使用开源软件 `WinSCP` 客户端, 对 FTPS 支持比较好。

开启 `FTPS 加密传输` 后, 会影响传输性能, 最大传输速度会降到 `50MiB/s` 左右。若对网络安全没那么高要求, 不建议加密。

---

## 👥 多用户配置

在主程序所在目录新建文件 `FtpServerUserList.csv` ，使用 `Excel` 或文本编辑器(需熟悉csv文件格式)编辑，一行一个配置：

1. 第一列：用户名，限定英文大小写/数字
2. 第二列：密码，限定英文大小写/数字/符号
1. 第三列：权限，详细配置如下。
1. 第四列：根目录路径

**📇 样例**

|           |        |           |              |
| --------- | ------ | --------- | ------------ |
| JARK006   | 123456 | readonly  | D:\Downloads |
| JARK007   | 456789 | readwrite | D:\Data      |
| JARK008   | abc123 | 只读      | D:\FtpRoot   |
| JARK009   | abc456 | elradfmwMT| D:\FtpRoot   |
| anonymous |        | elr       | D:\FtpRoot   |
| ...       |        |           |              |

注： anonymous 是匿名用户，允许不设密码，其他用户必须设置密码

📜 详细权限配置：

1. 使用 `readonly` 或 `只读` 设置为 `只读权限`。

1. 使用 `readwrite` 或 `读写` 设置为 `读写权限`。

1. 使用 `自定义` 权限设置, 从以下权限挑选自行组合(注意大小写): 

参考链接：https://pyftpdlib.readthedocs.io/en/latest/api.html#pyftpdlib.authorizers.DummyAuthorizer.add_user

📄 读取权限：
- `e` : 更改目录 (CWD 命令)
- `l` : 列出文件 (LIST、NLST、STAT、MLSD、MLST、SIZE、MDTM 命令)
- `r` : 从服务器检索文件 (RETR 命令)

📝 写入权限：
- `a` : 将数据附加到现有文件 (APPE 命令)
- `d` : 删除文件或目录 (DELE、RMD 命令)
- `f` : 重命名文件或目录 (RNFR、RNTO 命令)
- `m` : 创建目录 (MKD 命令)
- `w` : 将文件存储到服务器 (STOR、STOU 命令)
- `M` : 更改文件模式 (SITE CHMOD 命令)
- `T` : 更新文件上次修改时间 (MFMT 命令)

**📌 其他**

1. 若读取到有效配置，则自动 `禁用` 主页面的用户/密码设置。
2. 密码不要出现英文逗号 `,` 字符，以免和csv文本格式冲突。
3. 若不需要多用户配置，可将配置文件 `删除` 或`重命名` 为其他名称。
4. 配置文件可以是UTF-8或GBK编码。

---

## 🧩 使用到的库

1. [pyftpdlib](https://github.com/giampaolo/pyftpdlib)
2. [tkinter](https://docs.python.org/3/library/tkinter.html)
3. [pystray](https://github.com/moses-palmer/pystray)
4. [Pillow](https://github.com/python-pillow/Pillow)

---

## 🖼️ 预览

![](preview.png)