import ctypes
import json
import os
import socket
import platform
import time
from ctypes import *
import win32file

def send_data(host, port=5656):
    try:
        s = socket.socket()
        s.connect((host, port))
        return s
    except:
        print("网络错误!")
        return None


def get_free_space_mb(folder):
    """
    获取磁盘剩余空间
    :param folder: 磁盘路径 例如 D:\\
    :return: 剩余空间 单位 G
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        st = os.statvfs(folder)
        return st.f_bavail * st.f_frsize


def sort_rank(rank):
    for i in rank:
        for j in rank:
            if rank[i] < rank[j]:
                rank[i], rank[j] = rank[j], rank[i]
    return rank

def get_FileSize(filePath):
    fsize = os.path.getsize(filePath)
    return fsize


class sm3:
    def __init__(self):
        self.sm3dll = cdll.LoadLibrary('./sm3.dll')

    def return_res(self, out):
        return out.value.hex().upper()

    def sm3_file(self, path):
        while self.is_used(path):
            print("the file %s is using..." % path)
        path = create_string_buffer(path.encode(), len(path))
        buf = (c_char * 32)()
        #flag = self.sm3dll.sm3_file(path, byref(buf))
        flag = self.sm3dll.sm3_file(path, buf)
        while flag != 0:
            flag = self.sm3dll.sm3_file(path, buf)
        return self.return_res(buf)

    def cal_sm3(self, buf):
        output = (c_char * 32)()
        inp = create_string_buffer(buf.encode(), len(buf))
        flag = self.sm3dll.sm3(inp, len(buf), output)
        while flag != 0:
            flag = self.sm3dll.sm3(inp, len(buf), output)
        return self.return_res(output)

    def get_block_hash(self, path):
        f = open(path, "rb")
        f.read(32)
        buf = f.read(32)
        f.close()
        return buf.hex().upper()

    def is_used(self, file_name):
        try:
            vHandle = win32file.CreateFile(file_name, win32file.GENERIC_READ, 0, None, win32file.OPEN_EXISTING,
                                           win32file.FILE_ATTRIBUTE_NORMAL, None)
            return int(vHandle) == win32file.INVALID_HANDLE_VALUE
        except:
            return True
