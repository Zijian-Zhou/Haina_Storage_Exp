import time

from main import *

class test:
    def __init__(self):
        self.mutex = True

    def generatefile(self):
        src = open("source.dat", "ab+")
        for i in range(32768):
            src.write(bytes.fromhex("FEDCBA98765432100123456789ABCDEF"))
        src.close()


    def singel_file_upload_test(self):
        upload("source.dat", self)

    def singel_file_download_test(self):
        download(self)


    def test_file_range(self, max_size):
        cnt = 0
        while cnt < max_size:
            self.mutex = True
            self.generatefile()
            cnt += 0.5
            self.singel_file_upload_test()
            while self.mutex:
                continue
            self.mutex = True
            print("sleeping... ...")
            time.sleep(3)
            self.singel_file_download_test()
            while self.mutex:
                continue
