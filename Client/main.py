"""
This part is used for storage node's election and upload the data.


"""
import json
import os
import random
import threading
import time
from basefunctions import *
from ctypes import *


def upload(origin, test):
    data = open("test_file_range.csv", "a+")
    st = time.time()
    build_block().prepare(origin)
    et = time.time()
    data.write("%d, %s, " % (get_FileSize(origin), str(et-st)))
    ele = election(test)
    ele.start(origin)


def download(test):
    st = time.time()
    filedown = FileDownload()
    num = filedown.get_num()
    filedown.download()
    ready2rec(test, st, num)


if __name__ == "__main__":
    '''
    origin = "E:\\\\programing_projects\\\\paper_python_part\\\\Client\\\\pic.jpg"
    '''
    # upload("E:\\\\programing_projects\\\\paper_python_part\\\\Client\\\\pic.jpg")
    # download()
    from monitor import *

    test().test_file_range(200)
