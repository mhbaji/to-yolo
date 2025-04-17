import math
import os 
import json
import random 

def writeJson(data:dict, path:str):
    json_object = json.dumps(data, indent=4)
    with open(path, "w") as outfile:
        outfile.write(json_object)

def readJson(path:str):
    json_object = {}
    with open(path, 'r') as openfile:
        json_object = json.load(openfile)
    return json_object

def writeTxt(data:str, path:str):
    with open(path, "w") as writer: 
        writer.writelines(data) 

def readTxt(path:str):
    lines = []
    with open(path, 'r') as file:
        lines = file.readlines()
    return lines

def dirCheck(path:str, listCheck:list):
    res = False
    if os.path.isdir(path):
        dirs = os.listdir(path)
        dirs.sort()
        for il in listCheck:
            if not il in dirs:
                return res
        res = True
    return res 
