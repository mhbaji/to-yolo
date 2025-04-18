from lib.labelme import labelmeToYolo, yoloToLabelme

labelmeToYolo(
    "example",
    "example\\data.txt",
    "7,2,1",
    False 
)

yoloToLabelme(
    "example\\wajah"
)