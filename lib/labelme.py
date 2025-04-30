import datetime
import os
import shutil 
import math 
import random
import cv2 

from lib.tools import *

def toTxt(path, labelsFilePath):
    imagesFilePaths = []
    labels = readTxt(labelsFilePath)
    imagesPath = os.path.join(path, 'images')
    labelsPath = os.path.join(path, 'labels')
    labelmePath = os.path.join(path, 'labelme')
    if os.path.exists(imagesPath) and os.path.exists(labelmePath):
        if os.path.isdir(imagesPath) and os.path.isdir(labelmePath):
            if not os.path.exists(labelsPath):
                os.mkdir(labelsPath)

            imagesFiles = os.listdir(imagesPath)
            imagesFiles.sort()

            labelmeFiles = os.listdir(labelmePath)
            for iFile in imagesFiles:
                fileName, _ = os.path.splitext(iFile)
                jsonName = f"{fileName}.json"
                txtPath = os.path.join(labelsPath, f"{fileName}.txt")
                txtStr = ""
                if jsonName in labelmeFiles:
                    # konversi
                    jsonPath = os.path.join(labelmePath, jsonName)
                    jsonObject = readJson(jsonPath)
                    for shape in jsonObject['shapes']:
                        print(shape['label'], labels)
                        labelIdx = labels.index(shape['label'])
                        if shape['shape_type'] == 'rectangle':
                            xMin, yMin = None, None
                            xMax, yMax = None, None
                            for point in shape['points']:
                                xPoint, yPoint = point
                                if xMin is None or xMin > xPoint: xMin = xPoint
                                if yMin is None or yMin > yPoint: yMin = yPoint
                                if xMax is None or xMax < xPoint: xMax = xPoint
                                if yMax is None or yMax < yPoint: yMax = yPoint
                            xMid = (xMin + xMax)/2
                            yMid = (yMin + yMax)/2
                            width = xMax - xMin 
                            height = yMax - yMin 
                            xMidNorm = xMid/jsonObject['imageWidth']
                            yMidNorm = yMid/jsonObject['imageHeight']
                            widthNorm = width/jsonObject['imageWidth']
                            heightNorm = height/jsonObject['imageHeight']
                            _data_format = f"{labelIdx} {xMidNorm} {yMidNorm} {widthNorm} {heightNorm}\n"
                            txtStr += _data_format 

                        elif shape['shape_type'] == 'polygon':
                            _data_format = f"{labelIdx}"
                            for point in shape['points']:
                                xPoint, yPoint = point 
                                xPointNorm, yPointNorm = xPoint/jsonObject['imageWidth'], yPoint/jsonObject['imageHeight']
                                _data_format += f" {xPointNorm} {yPointNorm}"
                            _data_format += "\n"
                            txtStr += _data_format
                    
                writeTxt(txtStr, txtPath)
                iFilePath = os.path.join(imagesPath, iFile)
                absPath = os.path.abspath(iFilePath)
                imagesFilePaths.append(absPath)
    return imagesFilePaths, labels

def labelmeToYolo(path:str, labelsFilePath:str, ratio:str, isRemove:bool, dataName:str=""):
    ilList = ['images', 'labelme']
    tvList = ['train', 'val']
    if os.path.exists(path) and os.path.exists(labelsFilePath):
        if os.path.isdir(path) and os.path.isfile(labelsFilePath):
            # split dataset
            print("Splitting")
            if dirCheck(path, ilList) and not dirCheck(path, tvList):
                print(path)
                splitter(path, ratio, isRemove)

            elif not dirCheck(path, tvList):
                dirs = os.listdir(path)
                dirs.sort()

                for dir in dirs:
                    dsPath = os.path.join(path, dir)
                    if dirCheck(dsPath, ilList) and not dirCheck(dsPath, tvList):
                        print(dsPath)
                        splitter(dsPath, ratio, isRemove)
            print("Splitted")

            # convert
            print("Converting")
            data = {}
            labels = []
            if dirCheck(path, tvList):
                # tv dir
                dirs = os.listdir(path)
                dirs.sort()

                for dir in dirs:
                    tvPath = os.path.join(path, dir)
                    if dirCheck(tvPath, ilList):
                        print(tvPath)
                        data[dir], labels = toTxt(tvPath, labelsFilePath)

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
                                print(tvPath)
                                data[dsDir], labels = toTxt(tvPath, labelsFilePath)
            print("Converted")

            print("Set Dir Generating")
            setDirGenerator(data, labels, dataName)
            print("Done")
                    
def splitter(path:str, ratio:str, isRemove:bool):
    rSplit = ratio.split(",")
    fSplit = [float(x) for x in rSplit]
    if not sum(fSplit)==10: 
        print("Rasio Salah, Jika Dijumlah Harus Tepat 10")
        return 

    imagesPath = os.path.join(path, 'images')
    labelmePath = os.path.join(path, 'labelme')
    if (not os.path.exists(imagesPath) or not os.path.exists(labelmePath) or 
        not os.path.isdir(imagesPath) or not os.path.isdir(labelmePath)):
        return
    
    # get data list 
    imagesFiles = os.listdir(imagesPath)
    imagesFiles.sort()
    labelmeFiles = os.listdir(labelmePath)

    if len(imagesFiles) < 3:
        print("Data Terlalu Sedikit")
        return

    # data check 
    for iFile in imagesFiles:
        fileName, _ = os.path.splitext(iFile)
        jsonName = f"{fileName}.json"
        if not jsonName in labelmeFiles and isRemove:
            iFilePath = os.path.join(imagesPath, iFile)
            print(f"Hapus: {iFilePath}")
            os.remove(iFilePath)
    
    if isRemove:
        imagesFiles = os.listdir(imagesPath)
        imagesFiles.sort()

    # split
    print("Rasio Benar, Lanjut ke Konversi")
    lenData = len(imagesFiles)
    testCounts = math.ceil((fSplit[2]*lenData)/sum(fSplit))
    valCounts = math.ceil((fSplit[1]*lenData)/sum(fSplit))
    trainCounts = lenData - (testCounts+valCounts)

    sizes = [trainCounts, valCounts, testCounts]
    shuffled = random.sample(imagesFiles, len(imagesFiles))
    splitResult = []
    idx = 0
    for size in sizes:
        splitResult.append(shuffled[idx:idx+size])
        idx += size

    print('splitResult: ', splitResult)

    # create dir
    tvtList = ['train', 'val', 'test']
    ilList = ['images', 'labelme']
    dictPath = {}
    for tvt in tvtList:
        dictPath[tvt] = { "main": os.path.join(path, tvt) }
        if not os.path.exists(dictPath[tvt]['main']): os.mkdir(dictPath[tvt]['main'])

        for il in ilList:
            dictPath[tvt][il] = os.path.join(dictPath[tvt]['main'], il)
            if not os.path.exists(dictPath[tvt][il]): os.mkdir(dictPath[tvt][il])

    # copy file
    for idx, lData in enumerate(splitResult):
        for imName in lData:
            if idx == 0: 
                baseDestImageFile = dictPath['train']['images']
                baseDestLabelmeFile = dictPath['train']['labelme']
            elif idx == 1: 
                baseDestImageFile = dictPath['val']['images']
                baseDestLabelmeFile = dictPath['val']['labelme']
            elif idx == 2: 
                baseDestImageFile = dictPath['test']['images']
                baseDestLabelmeFile = dictPath['test']['labelme']

            sourceImageFile = os.path.join(imagesPath, imName)
            destImageFile = os.path.join(baseDestImageFile, imName)
            shutil.copy(sourceImageFile, destImageFile)
            
            imBaseName, _ = os.path.splitext(imName)
            jsonName = f"{imBaseName}.json"
            sourceLabelmeFile = os.path.join(labelmePath, jsonName)
            if os.path.exists(sourceLabelmeFile):
                destLabelmeFile = os.path.join(baseDestLabelmeFile, jsonName)
                shutil.copy(sourceLabelmeFile, destLabelmeFile)

def setDirGenerator(data:dict, labels:list, name:str=""):
    baseDir = "data"
    assert len(data) > 2, f"Data Tidak Sesuai, Hanya {data.keys()}"

    yamlFormat = {
        'train': "train.txt",
        'val': "val.txt",
        'test': "test.txt",
        'nc': len(labels),
        'names': labels 
    }
    _front_name = "data" if name == "" else name
    _timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    dirName = f"{_front_name} {_timestamp}"

    if not os.path.exists(baseDir): os.mkdir(baseDir)
    dirPath = os.path.join(baseDir, dirName)
    if not os.path.exists(dirPath): os.mkdir(dirPath)
        
    for key, val in data.items():
        imageString = "\n".join(val)
        if os.name == 'nt':
            imageString = imageString.replace("\\", "/")
        filePath = os.path.join(dirPath, f"{key}.txt")
        writeTxt(imageString, filePath)
    yamlPath = os.path.join(dirPath, "data.yaml")

    writeYaml(yamlFormat, yamlPath)

def toLabelme(path:str, labels:list):
    imagesPath = os.path.join(path, 'images')
    labelsPath = os.path.join(path, 'labels')
    labelmePath = os.path.join(path, 'labelme')
    if os.path.exists(imagesPath) and os.path.exists(labelsPath):
        if os.path.isdir(imagesPath) and os.path.isdir(labelsPath):
            if not os.path.exists(labelmePath):
                os.mkdir(labelmePath)

            imagesFiles = os.listdir(imagesPath)
            imagesFiles.sort()

            labelsFiles = os.listdir(labelsPath)
            for iFile in imagesFiles:
                fileName, _ = os.path.splitext(iFile)
                txtName = f"{fileName}.txt"

                if txtName in labelsFiles:
                    imagePath = os.path.join(imagesPath, iFile)
                    imageFile = cv2.imread(imagePath)
                    hFrame, wFrame = imageFile.shape[:2]

                    jsonFormat = {
                        "version": "5.5.0",
                        "flags": {},
                        "shapes": [],
                        "imagePath": f"../images/{iFile}",
                        "imageData": None,
                        "imageHeight": hFrame,
                        "imageWidth": wFrame
                    }

                    txtPath = os.path.join(labelsPath, txtName)
                    txtFile = readTxt(txtPath)
                    for tFile in txtFile:
                        tList = tFile.split(" ")
                        if len(tList) == 5:
                            xMid = float(tList[1])*wFrame
                            yMid = float(tList[2])*hFrame
                            width2 = (float(tList[3])*wFrame)/2
                            height2 = (float(tList[4])*hFrame)/2
                            xMin = xMid - width2
                            yMin = yMid - height2
                            xMax = xMid + width2
                            yMax = yMid + height2

                            shapesFormat = {
                                "label": labels[int(tList[0])],
                                "points": [
                                    [ xMin, yMin ],
                                    [ xMax, yMax ]
                                ],
                                "group_id": None,
                                "description": "",
                                "shape_type": "rectangle",
                                "flags": {},
                                "mask": None
                            }
                            jsonFormat['shapes'].append(shapesFormat)
                    
                    jsonPath = os.path.join(labelmePath, f"{fileName}.json")
                    writeJson(jsonFormat, jsonPath)

def yoloToLabelme(path:str):
    yamlPath = os.path.join(path, 'data.yaml')
    assert os.path.exists(yamlPath), "File Yaml Tidak Ditemukan"
    
    ilList = ['images', 'labels']
    tvList = ['train', 'val']

    yamlObject = readYaml(yamlPath)
    print("Converting")
    if dirCheck(path, ilList) and not dirCheck(path, tvList):
        print(path)
        toLabelme(path, yamlObject['names'])

    elif dirCheck(path, tvList):
        # tv dir
        dirs = os.listdir(path)
        dirs.sort()

        for dir in dirs:
            tvPath = os.path.join(path, dir)
            if dirCheck(tvPath, ilList):
                print(tvPath)
                toLabelme(tvPath, yamlObject['names'])

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
                        print(tvPath)
                        toLabelme(tvPath, yamlObject['names'])
    print("Done")