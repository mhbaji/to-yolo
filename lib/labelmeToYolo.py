import os
import shutil 
import math 
import random 

from lib.tools import *

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
                txtPath = os.path.join(labelsPath, f"{fileName}.txt")
                txtStr = ""
                if jsonName in labelmeFiles:
                    # konversi
                    jsonPath = os.path.join(labelmePath, jsonName)
                    jsonObject = readJson(jsonPath)
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

def labelmeToYolo(path:str, labelsFilePath:str, ratio:str, isRemove:bool):
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
            if dirCheck(path, tvList):
                # tv dir
                dirs = os.listdir(path)
                dirs.sort()

                for dir in dirs:
                    tvPath = os.path.join(path, dir)
                    if dirCheck(tvPath, ilList):
                        print(tvPath)
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
                                print(tvPath)
                                toTxt(tvPath, labelsFilePath)
            print("Converted")
                    
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
