import ctypes
import json
import os
import random
import socket
import platform
import threading
import time
from ctypes import *
import win32file

mistake_hash = "0000000000000000000000000000000000000000000000000000000000000000"
tds = []

def is_used(file_name):
    try:
        vHandle = win32file.CreateFile(file_name, win32file.GENERIC_READ, 0, None, win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_NORMAL, None)
        return int(vHandle) == win32file.INVALID_HANDLE_VALUE
    except:
        return True

def send_data(host, port=5656):
    try:
        s = socket.socket()
        s.connect((host, port))
        return s
    except:
        print("%s网络错误!" % host)
        return None


def get_free_space_mb(folder):
    """
    Get the free space of path
    :param folder: the path
    :return: free size KB
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        st = os.statvfs(folder)
        return st.f_bavail * st.f_frsize


def get_FileSize(filePath):
    fsize = os.path.getsize(filePath)
    return fsize


def sort_rank(rank):
    for i in rank:
        for j in rank:
            if rank[i] < rank[j]:
                rank[i], rank[j] = rank[j], rank[i]
    return rank


def ready2rec(test, st, num):
    meta = open("metafile.dat", "rb")
    meta.seek(32)
    source = meta.read(32).hex().upper()
    head = meta.read(32).hex().upper()

    re = recovery("downloads", head, num)
    re.start()
    election(test, st).clear_blocks(flag=True)


class election:

    def __init__(self, test, flag=None):
        # nodes records all the nodes, op_id records this time's event id
        if flag is not None:
            self.stime = flag
        else:
            self.stime = time.time()
        self.nodes = {}
        self.op_id = None
        self.block_num = len(os.listdir("cache")) - 1
        self.uploaded = []
        self.test = test

    # This function is used for checking the latest nodes file.
    def check_nodes(self):
        global mistake_hash
        res = sm3().sm3_file("nodes.dat")
        while res == mistake_hash:
            res = sm3().sm3_file("nodes.dat")
        # this value should get from a random node next!
        if "25B054C794EEEAB45188ED8C688E67A1198F84B4B31935F59E492ECE1FAD7D28" != res:
            return False
        else:
            return True

    # This function is used for selecting the header node
    def sele_headn(self):

        with open("nodes.dat", "r") as f:
            temp = f.read()
        temp = temp.split("\n")
        for i in temp:
            if i != "":
                self.nodes[i] = 0
        head = random.randint(0, len(self.nodes) - 1)
        head = list(self.nodes.keys())[head]

        return head

    """
    send2beginner is used for send the init data to the beginner node.
    :param node: beginner node ip
    :return: the new storage node
    """

    def send2beginner(self, node, blockseq, origin):
        """
        code "C000": inform the node to be the header node & get ready to the next election.
        data
            "this_size": the first data block's size
            "source": the original file's SM3 hash value
            "op_id": this time's event id, calculated by SM3, the parameters are source and the timestamp
            "newbk_size": the next data block's size
        """
        global mistake_hash
        data = {"code": "C000", "data": {"this_size": 0, "source": 0, "op_id": 0, "newbk_size": 0}}

        firsiz = get_FileSize("cache\\\\cache_%d" % blockseq)
        if blockseq + 1 < self.block_num:
            newbk_size = get_FileSize("cache\\\\cache_%d" % (blockseq + 1))
        else:
            newbk_size = 0
        source = sm3().sm3_file(origin)
        while source == mistake_hash:
            source = sm3().sm3_file(origin)
        self.op_id = sm3().cal_sm3(source + str(time.time()))
        while self.op_id == mistake_hash:
            self.op_id = sm3().cal_sm3(source + str(time.time()))

        data["data"]["this_size"] = firsiz
        data["data"]["source"] = source
        data["data"]["op_id"] = self.op_id
        data["data"]["newbk_size"] = newbk_size
        s = send_data(node)
        s.send(json.dumps(data).encode())

        if s is not None:
            buf = s.recv(1024).decode()
            data.clear()
            data = json.loads(buf)
            if data["code"] != "S000":
                s.close()
                print("Code Error at S000!")
                return False
            elif data["data"]["status"] == 0:
                print("Header Node Error, the header refused the request!")
                s.close()
                return False
            elif data["data"]["status"] == 1:
                """
                code "C001": giving the acceptance result
                data 
                    "status": 0 / 1, 0: Refuse, 1: Accept
                    "op_id": consistent with the op_id of 'C000'
                    if status is 0, then:
                        "next": the reselected node
                """
                try:
                    data = s.recv(1024).decode()
                    data = json.loads(data)
                except:
                    print(data)
                    exit(1)
                if data["code"] != "S001":
                    print("Recv Error rank code!")
                    s.close()
                    return False
                elif data["data"]["op_id"] != self.op_id:
                    print("Recv Error op_id at the rank_list")
                    s.close()
                    return False
                rank = s.recv(100 + int(data["data"]["rank_size"]))
                rank = json.loads(rank.decode())
                if rank["code"] != "S002":
                    print("Recv Error rank-list code!")
                    s.close()
                    return False

                next_node = rank["rec"]
                rank = rank["rank"]

                data["code"] = "C001"
                data["data"] = {}
                data["data"]["op_id"] = self.op_id

                if self.check_node_rate(next_node):
                    # over rate
                    data["data"]["status"] = 0
                    next_node = self.get_new_node(rank)
                    data["data"]["next"] = next_node
                else:
                    data["data"]["status"] = 1
                s.send(json.dumps(data).encode())
                s.close()
                self.nodes[node] += 1
                td = threading.Thread(target=self.sendblock, args=(node, blockseq, self.op_id))
                td.start()
                while not td.is_alive():
                    td.start()
                global tds
                tds.append(td)
                self.send2other(next_node, blockseq + 1, origin)
                return True

    def clear_blocks(self, flag=None):
        if flag is None:
            files = os.listdir("cache")
            for i in files:
                os.remove(os.path.join("cache", i))
        else:
            files = os.listdir("downloads")
            for i in files:
                os.remove(os.path.join("downloads", i))
        etime = time.time()
        if flag is None:
            data = open("test_file_range.csv", "a+")
        else:
            data = open("download_out.csv", "a+")
        data.write(str(etime - self.stime) + ",\n")
        data.close()
        self.test.mutex = False

    """
        other block
    """

    def send2other(self, node, blockid, origin):

        if blockid >= self.block_num:
            return
        if node is None:
            print("The node is None in ready to send")
            return
        self.send2beginner(node=node, blockseq=blockid, origin=origin)

    """
        If the node' selection is not good choice, then the get_new_node function
        will select the new storage node based on the rank-list's order & the node's rate.
        :param: rank: the nodes' rank list
        :return the new node
        if there aren't a new node satisfy the condition return None.
    """

    def get_new_node(self, rank, flag=True):
        if flag:
            for i in rank:
                if not self.check_node_rate(i) and self.nodes[i] == 0:
                    return i
            return self.get_new_node(rank, False)
        for i in rank:
            if not self.check_node_rate(i):
                return i

    """
    This function is used for checking the node's rate.
    As a default the rate is 20%.
    :param: node: the node that ready to calculate
    :param: stander: the rate stander with default value 20%.
    :return: A bool value, True: overflow, False: not overflow
    """

    def check_node_rate(self, node, stander=0.6):
        cnt = self.nodes[node]
        if cnt == 0:
            return False
        rate = (cnt + 1) / self.block_num
        if rate > stander:
            return True
        else:
            return False

    """
    sendblock is used for send the a block's data to a node after the node confirmed.
    :param node: the confirmed node
    :param blockid: identification of the block
    :param session: the event_id ( generated at the operation C000)
    """

    def sendblock(self, node, blockid, session=None, errortime=0):
        print("send block %d to %s" % (blockid, node))
        global mistake_hash
        be = time.time()
        req = {}

        path = "cache\\\\cache_%d" % blockid
        size = get_FileSize(path)

        bkh = sm3().sm3_file(path)
        while bkh == mistake_hash:
            time.sleep(0.3)
            bkh = sm3().sm3_file(path)
        temp = sm3().get_block_hash(path)
        while temp == mistake_hash:
            temp = sm3().get_block_hash(path)

        # ready upload
        s = send_data(node)
        while s is None:
            s = send_data(node)
        req["code"] = "F000"
        # base = 1500
        if session is not None:
            req["op_id"] = session
        else:
            print("Uoload block" + blockid + " failed, due to without session.")
            s.close()
            return
        req["bk_id"] = bkh
        req["temp"] = temp
        req["bk_size"] = size
        req["base"] = size
        base = size
        s.send(json.dumps(req).encode())

        time.sleep(0.005)

        f = open(path, "rb")

        cnt = 0
        while (cnt + base) < size:
            buf = f.read(base)
            s.send(buf)
            cnt += base

        if size - cnt > 0:
            buf = f.read(size - cnt)
            s.send(buf)

        f.close()
        s.close()

        inf = {}
        s = send_data(node)
        inf["code"] = "FC07"
        inf["block"] = temp
        inf["bk_id"] = bkh
        s.send(json.dumps(inf).encode())
        status = s.recv(1024)
        status = json.loads(status.decode())

        end = time.time()
        '''
        if status["code"] == 1:
            print("block %d send time is %f" % (blockid, end - be + errortime))
            s.close()
            self.uploaded.append(blockid)
            print("lenth: ", len(self.uploaded))
            if len(self.uploaded) == self.block_num:
                self.clear_blocks()
        else:
            print("status: ", status)
            print("The block has been broken during the upload process, reload now to the block %d" % blockid)
            print("The block %d hash is %s, and the node is %s" % (blockid, bkh, node))
            errortime += 1
            td = threading.Thread(target=self.sendblock, args=(node, blockid, self.op_id, end - be))
            global tds
            tds.append(td)
            td.start()
            while not td.is_alive():
                td.start()
        '''
        if status["code"] == 1:
            print("block %d check successful" % blockid)
        else:
            print("block %d failed to check" % blockid)

        self.uploaded.append(blockid)
        if len(self.uploaded) == self.block_num:
            self.clear_blocks()

        exit(0)

    """
    Begin to election and transmission
    """

    def start(self, origin):
        if not self.check_nodes():
            print("NODES HASH ERROR!")
            # get new nodes from network
            pass
        global mistake_hash
        head = self.sele_headn()

        f = open("metafile.dat", "ab+")

        path = "cache\\\\cache_0"
        bkh = sm3().get_block_hash(path)
        while bkh == mistake_hash:
            bkh = sm3().get_block_hash(path)
        source = sm3().sm3_file(origin)
        while source == mistake_hash:
            source = sm3().sm3_file(origin)

        f.write(bytes.fromhex(source))
        f.write(bytes.fromhex(bkh))
        f.write(head.encode())
        f.write(("\n"+str(self.block_num)).encode())
        f.close()
        self.send2beginner(head, 0, origin)
        rec = open("rec/%s.dat" % time.time(), "w")
        rec.write(json.dumps(self.nodes))
        rec.close()


class FileDownload:
    def __init__(self):
        f = open("metafile.dat", "rb")
        self.mask = f.read(32)
        self.source = f.read(32).hex().upper()
        self.first = f.read(32).hex().upper()
        f.close()
        f = open("metafile.dat", "r", encoding="utf-8")
        f.seek(96)
        self.header = f.read()
        print(self.header)
        self.header, self.num = self.header.split("\n")
        f.close()
        self.finished = False
        self.found = 0
        self.downloaded = 0

    def get_num(self):
        return self.num

    def find_block(self, hash):
        with open("nodes.dat", "r") as f:
            nodes = f.read().split("\n")

        for i in nodes:
            if i == "":
                continue
            td = threading.Thread(target=self.ask, kwargs={"hash": hash, "i": i})
            td.start()

    def get_block_inf(self, block):
        p = block.read(32)
        c = block.read(32)
        n = block.read(32)
        return p, c, n

    def rebuild_block(self, block):
        block_hash = block[block.find("down_") + 5:block.find("down_") + 69]
        cache_path = "recache_%s" % block_hash

        src = open(block, "rb")
        cache = open(cache_path, "wb")

        src_inf = list(self.get_block_inf(src))
        cache_inf = [""] * 3

        for i in range(32):
            temp0 = hex(src_inf[0][i] ^ self.mask[i])
            temp2 = hex(src_inf[2][i] ^ self.mask[i])
            if len(temp0) == 4:
                cache_inf[0] += temp0[2::].upper()
            else:
                cache_inf[0] += "0" + temp0[2::].upper()

            if len(temp2) == 4:
                cache_inf[2] += temp2[2::].upper()
            else:
                cache_inf[2] += "0" + temp2[2::].upper()

        cache_inf[0] = bytes.fromhex(cache_inf[0])
        cache_inf[2] = bytes.fromhex(cache_inf[2])

        cache.write(cache_inf[0])
        cache.write(src_inf[1])
        cache.write(cache_inf[2])
        cache.write(src.read())

        cache.close()
        src.close()

        os.remove(block)
        os.rename(cache_path, block)
        exit(0)

    def p2p_get1(self, block_hash, loc):
        print(block_hash, loc)
        global mistake_hash
        path = "downloads\\down_%s.dat" % block_hash
        data = {}
        s = send_data(loc)
        data["code"] = "F006"
        data["block"] = block_hash
        s.send(json.dumps(data).encode())

        res = s.recv(1024)
        res = json.loads(res.decode())

        if res["code"] != "F007":
            print("The node given an error code.")
            return

        base = res["base"]
        size = res["block_size"]

        while True:
            f = open(path, "wb+")

            cnt = 0
            while (cnt + base) < size:
                f.write(s.recv(base))
                cnt += base
                time.sleep(0.0005)

            if size - cnt > 0:
                f.write(s.recv(size - cnt))

            f.close()
            recv_fh = sm3().get_block_hash(path)
            while recv_fh == mistake_hash:
                recv_fh = sm3().get_block_hash(path)
            res.clear()
            res["code"] = "F008"
            if block_hash == recv_fh:
                res["status"] = 1
                s.send(json.dumps(res).encode())
                break
            else:
                res["status"] = 0
                s.send(json.dumps(res).encode())
        s.close()

        f = open(path, "rb")
        f.seek(64)
        next = f.read(32)
        f.close()

        ans = ""

        for i in range(32):
            temp = hex(next[i] ^ self.mask[i])
            if len(temp) == 4:
                ans += temp[2::].upper()
            else:
                ans += "0" + temp[2::].upper()
        next = ans
        td = threading.Thread(target=self.rebuild_block, kwargs={"block": path})
        td.start()

        self.downloaded += 1
        print(self.downloaded, self.num, self.found)
        if int(self.downloaded) == int(self.num):
            print("end")
            self.finished = True

        if self.first != next:
            self.find_block(next)

    def ask(self, hash, i):
        data = {"code": "F003", "ask": hash}
        s = send_data(i)
        s.send(json.dumps(data).encode())
        ans = s.recv(1024)
        s.close()
        ans = json.loads(ans.decode())

        if ans["code"] != "F004":
            print("The node given an error code in asking the block.")
            exit(0)

        if ans["statu"] == 1:
            self.found += 1
            self.p2p_get1(hash, i)

        exit(0)

    def download(self, ):
        data = {}
        s = send_data(self.header)
        data["code"] = "F002"
        data["block_hash"] = self.first

        s.send(json.dumps(data).encode())
        res = s.recv(1024)
        res = json.loads(res.decode())
        s.close()

        if res["is_get"] == 1:
            # td = threading.Thread(target=self.p2p_get, args=(self.first, res["loc"]))
            # td.start()
            self.p2p_get1(self.first, res["loc"])
        else:
            print("The file lost!")

        while not self.finished:
            continue


class sm3:
    def __init__(self):
        self.sm3dll = cdll.LoadLibrary('./sm3.dll')

    def return_res(self, out):
        res = ""
        for i in out:
            temp = hex(i)
            if len(temp) == 4:
                res += str(hex(i))[2::]
            else:
                res += "0" + str(hex(i))[2::]
        return res.upper()

    def sm3_file(self, path):
        path = create_string_buffer(path.encode(), len(path))
        buf = (c_ubyte * 32)()
        self.sm3dll.sm3_file(path, byref(buf))
        return self.return_res(buf)

    def cal_sm3(self, buf):
        output = (c_ubyte * 32)()
        inp = create_string_buffer(buf.encode(), len(buf))
        self.sm3dll.sm3(inp, len(buf), byref(output))
        return self.return_res(output)

    def get_block_hash(self, path):
        f = open(path, "rb")
        f.read(32)
        buf = f.read(32)
        f.close()
        return buf.hex().upper()


"""
    This class is designed for recovery the encrypted file.
    New this class needs 2 parameters respectively, the downloaded cache path
    and the head block's hash value.
    Run the start() function only to get start with processing.
"""


class recovery:
    """
        :param: cachepath:  str, the downloaded block cache's directory's path
        :param: headhashL:  hex str, the head block's hash value
        class global parameters:
            :param self.capath:     str, the downloaded block cache's directory's path
            :param self.head:       str, the head block hash value of SM3
            :param self.files:      list, at the beginning, it's the all the downloaded cache's paths.
                            It's converted to dict-list when the function construct() called, each
                            item is a dictionary, in the item, there are 4 key-value pairs:
                                * "path":   the block's physical path
                                * "pre":    previous block's SM3 hash value
                                * "cur":    this block's hash value of SM3
                                * "next":   the next block hash value
            :param block_inf: list, the original block's order

    """

    def __init__(self, cachepath, headhash, num):
        self.capath = cachepath
        self.head = headhash
        self.files = os.listdir(self.capath)
        while int(num) > len(self.files):
            self.files = os.listdir(self.capath)
            print("len:", len(self.files))
        self.block_inf = []
        self.offset = None
        self.key = ""

    """
        It is a recursive function which truly construct the block_inf's order.
        Input:
            :param hash:    hex str, the block's hash which ready to insert.
            :param flag:    bool, the function begin flag.
                                False: Function has not be started.
                                True: Function has been called.
            :param id:      int, the index in the self.files
    """

    def find(self, hash, flag, id):
        # checking the cycle has been traversed.
        if hash == self.head and flag:
            return

        # append into the order
        self.block_inf.append(self.files[id]["path"])

        # traver the self.files to find the next block
        for i in range(len(self.files)):
            if self.files[i]["cur"] == self.files[id]["next"]:
                nextid = i
                break

        # append the next block
        self.find(self.files[id]["next"], True, nextid)

    """
        This function is used for getting a block's inf.
        Input:
            :param path:    str, the block's physical directory
        Output:
            :param inf:     dictionary, the block's inf which ready to be a item in the self.files
    """

    def __get_inf(self, path):
        # init
        inf = {"path": path, "pre": "", "cur": "", "next": ""}
        while inf["pre"] == "" or inf["cur"] == "" or inf["next"] == "":
            if is_used(path):
                time.sleep(1)
                continue
            f = open(path, "rb")
            inf["pre"] = f.read(32).hex().upper()  # the previous block hash value
            inf["cur"] = f.read(32).hex().upper()  # the current block hash value
            inf["next"] = f.read(32).hex().upper()  # the next block hash value
            f.close()
        return inf

    """
        The construction is prepared for recovering the original block order.
        There 2 steps respectively.
        The 1st step is preparing the all the blocks' information to the self.files.
        The 2ed step is get the order with each block's hash values information.
    """

    def construct(self):
        # :param length:    int, the block's amount
        # :param headid:    int, the head block's index in the self.files
        length = len(self.files)
        headid = None

        # travel the self.files, to get all the blocks' information
        for i in range(length):
            #   get the full path
            path = os.path.join(self.capath, self.files[i])
            #   get the block inf
            self.files[i] = self.__get_inf(path)
            # checking the head block
            if self.files[i]['cur'] == self.head:
                headid = i

        # the 2ed step
        self.find(self.files[headid]["cur"], False, headid)

    """
        this function is designed for appending a block to recovery file.
        :param src: str, the ready to append block's path
        :param dst: file obj, the recovery file
    """

    def append_block(self, src, dst, idx):
        tof = open(src, "rb")
        # passing by the hash pointer domain
        tof.seek(96 + self.offset[idx], 0)
        # reading the remain data to write in the recovery file
        buf = tof.read()
        dst.write(buf)
        tof.close()

    def __get_key(self):
        files = []
        key = ""
        for i in self.block_inf:
            files.append(open(i, "rb"))

        cnt = -1
        leng = len(self.block_inf)
        self.offset = [0] * leng
        for i in range(32):
            mod = i % leng
            if mod == 0 and 32 / leng > mod:
                cnt += 1

            files[mod].seek(96 + cnt)
            buf = files[mod].read(1)
            self.offset[mod] += 1
            key += buf.hex().upper()

        for i in files:
            i.close()

        self.key = key

    """
        rebuilding the encryption file
    """

    def rebuild(self):
        self.__get_key()
        f = open("download.dat", "wb")
        # constructing the recovery file according to the original block order
        for i in self.block_inf:
            self.append_block(i, f, self.block_inf.index(i))
        f.close()

    def decrypt(self):
        keyfile = open("key.temp", "wb+")
        key = bytes.fromhex(self.key)
        keyfile.write(key)
        keyfile.close()
        build_block(True).decryption()

    """
        getting start
    """

    def start(self):
        self.construct()
        self.rebuild()
        self.decrypt()


class build_block:
    def __init__(self, flag=None):
        if flag is None:
            self.dll = cdll.LoadLibrary('./encryption.dll')
        else:
            self.dll = cdll.LoadLibrary('./encryptionbak.dll')

    def trans2ct(self, str):
        return create_string_buffer(str.encode(), len(str))

    def prepare(self, path):
        path = self.trans2ct(path, 10)
        self.dll.init(path)

    def decryption(self):
        download = self.trans2ct("download.dat")
        output = self.trans2ct("decryption.dat")
        key = self.trans2ct("key.temp")
        self.dll.decrypt(download, output, key)
