# HaiNa Storage: A Novel Decentralized Storage System （Experimental Version For Paper）

# 海纳存储：一种新型去中心化云存储系统(论文实验版本)


---
 
This repository is the experimental codes for the Haina storage paper. The engineering prototype is in the repository [HNS](https://github.com/Zijian-Zhou/Haina_Storage).
 
本仓库为海纳存储论文实验代码，工程原型系统请参见[HNS](https://github.com/Zijian-Zhou/Haina_Storage)。

---

# Introduction (简介)

In this repository, there are two folders for client and server respectively. We prefer you run these codes on Windows, becaues we implement and test it on Windows platform.

在本仓库中，有两个文件夹，分布对应着客户端和服务器程序。因为我们代码开发和测试都是在Windows上，因此建议您在Windows系统上运行相关代码。

# Preparation （预备工作）

There are some dependencies we need. Despite ``pymysql`` lib we do not really use it in the codes, but we involve some interfaces in our codes because using a database is our initial imagination.

以下库需要提前安装。其中``pymysql``并没有实际在我们的代码中使用，但保留了一些接口在代码中，因为我们一开始打算用数据库做扩展。

```shell
pywin32
pymysql
```

Besides, there is a same file ``nodes.dat`` both in client and server folders. Before you run the client and server program, you need to change the records in the file. The file include ``n`` lines. Each line records the ip address of different peer nodes.

此外，在客户端和服务器端目录中，存在一个相同的文件``nodes.dat``用于记录所有节点信息。这个节点文件由``n``行组成，每行一个ip地址。

```shell
ip1
ip2
...
ipn
```

# Run (运行)

## Client (客户端)

In the client program, we provide a ``.bat`` file that you can directly click to run the program. As a default, we fix the test range of file size from``0.5 MB`` to ``200 MB`` by an increase of ``0.5 MB``. You can change it by editing the 41st line in main.py. The experiment records will be written into a CSV file ```test_file_range.csv```. In the running process, it will generate a ``source.dat`` file. Delete it before you start a new experiment because the ``source.dat`` is the file that the program tries to store. The increase will append to it if you do not delete it.

在客户端程序中，我们提供了一个``.bat``文件，您可以直接点击运行程序。默认情况下，我们将文件大小的测试范围固定为从``0.5 MB``到``200MB``，每次增加``0.5 MB``。您可以通过编辑``main.py``中的第41行来更改它。实验记录将写入CSV文件``test_file_range.csv``。在运行过程中，它将生成一个``source.dat``文件。在开始新的实验之前，请先将其删除，因为``source.dat``是程序尝试存储的文件。如果您不删除它，增加的内容将附加到它后面。

```python
test().test_file_range(200)
```

You can edit the 829th line at ``basefunctions.py`` to change the amount of blocks.

您可以修改 ``basefunctions.py`` 的第829行，从而改变分块数量。

```python
path = self.trans2ct(path, 10)
```

## Server （服务器端）

There is nothing to be noted except the start way. We provide the ``start.bat`` to help you start the server program. But it will do not work on your computer, because you need to change the local ip address of your host. The parameters (n, w, d) are not really uesed, therefore you can fill it arbitrarily but you must fill it. Parameter ``i`` present the local ip address of your host and the parameter ``p`` is the server port of the program. You do NOT recommend you to change the port.

除了启动方式，没有什么需要注意的。我们提供了``start.bat``来帮助您启动服务器程序。但是它不会在您的电脑上工作，因为您需要更改主机的本地ip地址。参数（n，w，d）实际上用不到，因此您可以随意填写，但必须填写。参数``i``表示主机的本地ip地址，参数``p``是程序的服务器端口。不建议您更改端口。


```shell
python main.py -i 192.168.10.128 -p 5656 -n test -w test -d test
```
