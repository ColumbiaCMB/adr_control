import logging
import time
import sys

class MessageFile():
    def __init__(self,method=None):
    
        ### Eventually add custom file creation/naming like data_logger here.###
        
        if method != None:
            self.passer=Passer(method)
    
        self.logger=logging.getLogger('message_logger')
        self.logger.setLevel(logging.DEBUG)
        self.formatter=logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.file_handler=logging.FileHandler(filename='example.log')
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        #self.stream_handler=logging.StreamHandler(sys.stdout)
        self.stream_handler=logging.StreamHandler(self.passer)
        self.stream_handler.setLevel(logging.DEBUG)
        self.stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.stream_handler)
        
    def log(self,message):
        self.logger.info(message)
        
    def debug_log(self,message):
        self.logger.debug(message)
        
class Passer():
    def __init__(self,method):
        self.target=method
    def write(self,message):
        self.target(message)
    def flush(self):
        return
        
