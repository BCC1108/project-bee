import os
import pathlib
from configparser import ConfigParser


# 获取欧易的apikey和secret
def getOkApiKey(k, s, p):
    config = ConfigParser()
    config_file_path = os.path.join(
        pathlib.Path(__file__).parent.resolve(), ".", "config.ini"
    )
    config.read(config_file_path , encoding="utf-8") #手动指定编码格式
    return config["keys"][k], config["keys"][s], config["keys"][p]
