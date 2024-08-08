import numpy as np
import csv
import os
import datetime
import sys

scriptDir = os.path.dirname(__file__)
CSV_PATH = scriptDir + "\\csvFiles\\"

def getCurrentTime():
    return datetime.datetime.now().isoformat()

def appendToCSV(data, fileName):
    filePath =  CSV_PATH + fileName + ".csv"
    fileExists = os.path.isfile(filePath)

    with open(filePath, "a", newline="") as file:
        writer = csv.writer(file)

        # Write header on nonexisting file
        if not fileExists:
            writer.writerow(["dateID", "imgInfo", "speckleData"])

        writer.writerows(data)

def readCSV(fileName):
    maxInt = sys.maxsize
    while True:
    # decrease the maxInt value by factor 10 
    # as long as the OverflowError occurs.
        try:
            csv.field_size_limit(maxInt)
            break
        except OverflowError:
            maxInt = int(maxInt/10)

    filePath =  CSV_PATH + fileName + ".csv"
    with open(filePath, "r", newline="") as file:
        reader = csv.reader(file)
        data = [row for row in reader]

    # Delete header
    return np.array(data[1:])