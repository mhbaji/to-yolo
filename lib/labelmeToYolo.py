import os 
import json 

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

def toTxt(path, labelsFilePath):
    imagesPath = os.path.join(path, 'images')
    labelsPath = os.path.join(path, 'labels')
    labelmePath = os.path.join(path, 'labelme')
    if os.path.exists(imagesPath) and os.path.exists(labelmePath):
        if os.path.isdir(imagesPath) and os.path.isdir(labelmePath):
            labels = readTxt(labelsFilePath)
            if not os.path.exists(labelsPath):
                os.mkdir(labelsPath)

            imagesFiles = os.listdir(imagesPath)
            imagesFiles.sort()

            labelmeFiles = os.listdir(labelmePath)
            for iFile in imagesFiles:
                fileName, _ = os.path.splitext(iFile)
                jsonName = f"{fileName}.json"
                if jsonName in labelmeFiles:
                    # konversi
                    jsonPath = os.path.join(labelmePath, jsonName)
                    txtPath = os.path.join(labelsPath, f"{fileName}.txt")

                    jsonObject = readJson(jsonPath)
                    txtStr = ""
                    for shape in jsonObject['shapes']:
                        if shape['shape_type'] == 'rectangle':
                            xMin, yMin = shape['points'][0]
                            xMax, yMax = shape['points'][1]
                            xMid = (xMin + xMax)/2
                            yMid = (yMin + yMax)/2
                            width = xMax - xMin 
                            height = yMax - yMin 
                            xMidNorm = xMid/jsonObject['imageWidth']
                            yMidNorm = yMid/jsonObject['imageHeight']
                            widthNorm = width/jsonObject['imageWidth']
                            heightNorm = height/jsonObject['imageHeight']
                            labelIdx = labels.index(shape['label'])
                            _data_format = f"{labelIdx} {xMidNorm} {yMidNorm} {widthNorm} {heightNorm}\n"
                            txtStr += _data_format
                    
                    writeTxt(txtStr, txtPath)

def labelmeToYolo(path:str, labelsFilePath:str):
    ilList = ['images', 'labelme']
    tvList = ['train', 'val']
    if os.path.exists(path) and os.path.exists(labelsFilePath):
        if os.path.isdir(path) and os.path.isfile(labelsFilePath):
            if dirCheck(path, ilList):
                # il dir
                toTxt(path, labelsFilePath)

            elif dirCheck(path, tvList):
                # tv dir
                dirs = os.listdir(path)
                dirs.sort()

                for dir in dirs:
                    tvPath = os.path.join(path, dir)
                    if dirCheck(tvPath, ilList):
                        toTxt(tvPath, labelsFilePath)

            else:
                # dataset dir
                dirs = os.listdir(path)
                dirs.sort()

                for dir in dirs:
                    dsPath = os.path.join(path, dir)
                    if dirCheck(dsPath, tvList):
                        dsDirs = os.listdir(dsPath)
                        dsDirs.sort()

                        for dsDir in dsDirs:
                            tvPath = os.path.join(dsPath, dsDir)
                            if dirCheck(tvPath, ilList):
                                toTxt(tvPath, labelsFilePath)
