import numpy as np
import rawpy
from scipy import ndimage
import cv2
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from rawProcessor import processRawImagePair, processRawImage, RAW_FORMATS
import dataManager

'''
---- Vorverarbeitung der Bilder ----
1. Das Referenz- und Specklebild werden eingelesen.
    - Die RAW-Daten werden normalisiert und entsprechend der angegebenen Farbe debayert.
2. Der hellste Bereich im Specklebild wird gefunden und aus beiden Bildern ausge-schnitten.
3. Die Perforationen werden entfernt.
    - Der Nutzer wählt den Schwellwert zur Maskierung der Perforationen aus dem Referenzbild. Die erstellte Maske wird für beide Bilder verwendet.

---- Errechnen des Speckles ----
1. Der gefilterte Speckle für das Referenzbild wird errechnet.
2. Der rohe, gefilterte und finale Speckle für das Specklebild werden errechnet.
'''

# ------------------------
# - ACTIVATION FUNCTIONS -
# ------------------------

# Main function to start the speckle calculation
def analyzeImage(path, refName, imgName, datatype, useRefImg=True, debayerChannel="g", metadata={}, saveFileName=None):
    print("__________________")
    print("Loading and processing image '"+ imgName + "' " + "[" + datatype + "]" + "...")
    rawTypes = list(RAW_FORMATS.values())

    refPath = path + refName + "." + datatype
    imgPath = path + imgName + "." + datatype
    metadata["color"] = debayerChannel 

    # Preprocess images based on datatype
    # RAW: Normalisation, custom single-channel debayering
    # Other: Get a single color channel from RGB image
    if datatype in rawTypes: 
        # RAW processing 
        if useRefImg:
            with rawpy.imread(imgPath) as rawImg, rawpy.imread(refPath) as rawRef:
                img, refImg = processRawImagePair(rawImg, rawRef, debayerChannel)
        else:
            with rawpy.imread(imgPath) as rawImg:
                img = processRawImage(rawImg, debayerChannel)
    else:
        # Standard processing (JPG, PNG)
        # Process reference image
        if useRefImg:
            refImg = cv2.imread(refPath)
            if refImg is not None:
                r, g, b = cv2.split(refImg)
                refImg = g if debayerChannel=="g" else r if debayerChannel=="r" else b
        
        # Process speckle image
        img = cv2.imread(imgPath)
        r, g, b = cv2.split(img)
        img = g if debayerChannel=="g" else r if debayerChannel=="r" else b

    # Call speckle calculation
    if useRefImg:
        results = calculateProjectionSpeckle(refImg, img)
    else:
        results = calculateProjectionSpeckle(None, img, useRefImg)

    # Generate csv-data and save to csv if a save-name is given
    if type(saveFileName) == type("STRING"):
        if(saveFileName != ""):
            imgData = {"name": imgName, "datatype": datatype, "path": imgPath}
            dataToSave = [dataManager.getCurrentTime(), imgData, results, metadata]
            dataManager.appendToCSV([dataToSave], saveFileName)

# Same as analyzeImage() without the need to handel the refImage in any way 
def analyzeImageNoRef(path, imgName, datatype, debayerChannel="g", metadata={}, saveFileName=None):
    analyzeImage(path, "", imgName, datatype, useRefImg=False, debayerChannel=debayerChannel, metadata=metadata, saveFileName=saveFileName)

# Simplified function to call if a single image should be processed
def analyzeSingleMeasurement(measurement):
    analyzeMeasurementBatch([measurement])

# Simplified function to call if multiple images should be processed after one another
def analyzeMeasurementBatch(measuerementBatch):
    for measurement in measuerementBatch:
        path = measurement["path"]
        refName = measurement["refName"] if "refName" in measurement else ""
        imgName = measurement["imgName"]
        datatype = measurement["datatype"]
        useRefImg = measurement["useRefImg"] if "useRefImg" in measurement else "True"
        debayerChannel = measurement["debayerChannel"] if "debayerChannel" in measurement else "g"
        metadata = measurement["metadata"] if "metadata" in measurement else {}
        saveFileName = measurement["saveFileName"] if "saveFileName" in measurement else None
        
        analyzeImage(path, refName, imgName, datatype, useRefImg, debayerChannel, metadata, saveFileName)

# -----------------
# - KEY FUNCTIONS -
# -----------------

# Finds the brightest area (based on given size) in an image 
# Returns a filter that can be used to crop images using the cropImage(img, cropFilter) method
def findBrightestArea(image, areaSize, debug=False):
    # Calculate integral image
    integralImage = cv2.integral(image)
    areaWidth, areaHeight = areaSize

    # Calculate sum of given area
    def sumArea(integralImg, x, y, w, h):
        botRight = integralImg[y+h, x+w]
        botLeft = integralImg[y+h, x]
        topRight = integralImg[y, x+w]
        topLeft = integralImg[y, x]
        return botRight - botLeft - topRight + topLeft
    
    maxSum = maxX = maxY = -1
    imgHeight, imgWidth = image.shape[:2]

    # Slide a window over the image and find the max sum
    for y in range(imgHeight - areaHeight + 1):
        for x in range(imgWidth - areaWidth + 1):
            currentSum = sumArea(integralImage, x, y, areaWidth, areaHeight)
            if currentSum > maxSum:
                maxSum = currentSum
                maxX, maxY = x, y

    if debug:
         # Highlight the brightest area on the original image
        brightestArea = image[maxY:maxY+areaHeight, maxX:maxX+areaWidth].copy()

        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        scale = 0.5
        cv2.rectangle(image, (maxX, maxY), (maxX + areaWidth, maxY + areaHeight), (0, 255, 0), 2)
        cv2.imshow('Image with brightest area highlighted', cv2.resize(image, (0,0), fx=scale, fy=scale))
        cv2.imshow('Brightest area', brightestArea)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    cropFilter = [maxX, maxY, areaWidth, areaHeight]
    return cropFilter

# Crops the given image based on the given crop filter
def cropImage(img, cropFilter):
    maxX, maxY, width, height = cropFilter
    return img[maxY:maxY+height, maxX:maxX+width].copy()

# Returns a perforation mask based on a given threshold
def getImagePerforationMask(img, threshold, erosionSize=2):
    _, perfMask = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    perfMask = cv2.erode(perfMask, np.ones((erosionSize,erosionSize), np.uint8))
    return perfMask

# Finds perforations in an image based on a brightness-threshold
def findPerforations(img):
    initialThreshold = 30
    perfMask = getImagePerforationMask(img, initialThreshold)
    updatedPerfMask = [perfMask]

    # Create plot
    fig, ax = plt.subplots()
    ax.imshow(perfMask, cmap='gray')
    fig.subplots_adjust(bottom=0.3)

    # Update mask on slider change
    def update(newThreshold):
        updatedPerfMask[0] = getImagePerforationMask(img, newThreshold)
        ax.imshow(updatedPerfMask[0], cmap='gray')
        fig.canvas.draw_idle()

    def close(event):
        plt.close(fig)

    # Create horizontal threshold-slider
    axfreq = fig.add_axes([0.18, 0.18, 0.65, 0.03])
    thresholdSlider = Slider(ax=axfreq,label='Threshold',valmin=1,valmax=255,valinit=initialThreshold)
    thresholdSlider.on_changed(update)

    # Create button to accept value
    axbutton = plt.axes([0.8, 0.03, 0.1, 0.075])
    button = Button(axbutton, 'Accept')
    button.on_clicked(close)

    plt.show()

    return updatedPerfMask[0] 

# Reduces a given 2D-Array to a 1D-Array. 
# A mask can be given to exclude pixels of the input-image from the flattened image    
def flattenImage(img, mask=None, debug=False):
    flat = []
    debugImg = []
    for idxY, y in enumerate(img):
        debugImg.append([])
        for idxX, x in enumerate(y):
            if type(mask) == type(None) or mask[idxY][idxX] > 0:
                flat.append(x)
                debugImg[idxY].append(int(x))
            else:
                debugImg[idxY].append(int(0))
    if debug:
        debugShowImg(debugImg, "Masked Image", debug)
    return flat


# Calculates the speckle contrast of a given image
def calculateSpeckleContrast(img):
    return np.std(img) / np.average(img) * 100


# Calculates the speckle values for the given image and returns them
def calculateProjectionSpeckle(refImage=None, speckleImage=None, useRefImg=True):
    
    # The area that the image is being cropped to is based on the width of the image
    imgWidth = np.array(speckleImage).shape[1]
    scaledCropSize = int(imgWidth/9)
    cropAreaHeight = cropAreaWith = scaledCropSize if scaledCropSize >= 400 else 400

    # -- CROPPING BASED ON BRIGHTEST AREA --
    # Find the brightest area and crop it out of the reference- and speckle-image
    print(" > Finding brightest area")
    cropFilter = findBrightestArea(speckleImage, (cropAreaHeight, cropAreaWith))
    if refImage is not None:
        refImageCropped = cropImage(refImage, cropFilter)
    speckleImageCropped = cropImage(speckleImage, cropFilter)

    # -- GENERATE PERFORATION MASK --
    # Generate perforation mask // Fill mask with white if there is no reference
    print(" > Generating perforation mask")
    perfMask = None
    if useRefImg:
        perfMask = findPerforations(refImageCropped)
    else:
        perfMask = np.full((cropAreaHeight, cropAreaWith), 255)

    print("\nResults:")

    # -- CALCULATE REFERENCE SPECKLE --
    if useRefImg:
        # Mask and flatten ref image
        refImgFlatMasked = flattenImage(refImageCropped, perfMask)

        # Highpass filter to remove global intensity variations
        kernelSize = 9
        imgLowPass = ndimage.gaussian_filter(refImgFlatMasked, kernelSize, mode = 'mirror')
        imgHighPass = np.divide(refImgFlatMasked,imgLowPass)

        # Calculate reference speckle
        refSpeckleFiltered = calculateSpeckleContrast(imgHighPass)
        printResultFormatted(refSpeckleFiltered, "Referencespeckle (filtered)")
    else:
        refSpeckleFiltered = -1

    # -----------------
    # Calculate Speckle
    # -----------------
    # Mask and flatten speckle image
    speckleImgFlatMasked = flattenImage(speckleImageCropped, perfMask, debug=False)

    # -- CALCULATE RAW SPECKLE --
    speckleRaw = calculateSpeckleContrast(speckleImgFlatMasked)
    printResultFormatted(speckleRaw, "Speckle (raw)")

    # Highpass filter to remove global intensity variations
    kernelSize = 9
    imgLowPass = ndimage.gaussian_filter(speckleImgFlatMasked, kernelSize, mode = 'mirror')
    if 0 in imgLowPass:
        imgLowPass += 1
    imgHighPass = np.divide(speckleImgFlatMasked,imgLowPass)
    
    # -- CALCULATE FILTERED SPECKLE --
    speckleFiltered = calculateSpeckleContrast(imgHighPass)
    printResultFormatted(speckleFiltered, "Speckle (filtered)")

    # -- CALCULATE FINAL SPECKLE --
    # Apply correction for reference speckle noise level
    # From: https://www.lipainfo.org/laser-illumination-sources/speckle-metrology/
    speckleCorrected = -1
    if useRefImg:
        Jefke = speckleFiltered**2 - refSpeckleFiltered**2
        if Jefke > 0:
            speckleCorrected = np.sqrt(Jefke)
            printResultFormatted(speckleCorrected, "Speckle (final)")
        else:
            speckleCorrected = -1
            print(" ! Reference speckle level higher than measured speckle level. Can't calculate 'Speckle (final)'")
    else:
        print(" ! No reference used. Can't calculate 'Speckle (final)'")
    
    return {"fi_ref_speck": refSpeckleFiltered, "raw_speck": speckleRaw, "fi_speck": speckleFiltered, "dif_speck": speckleCorrected, "ref_flattened": refImgFlatMasked, "speck_flattened": speckleImgFlatMasked}

# ---------------------
# - SUPPORT FUNCTIONS -
# ---------------------

# Opens a window and displays the given image
def debugShowImg(img, title="Debug", debug=True):
    if debug:
        cv2.imshow(title, np.array(img))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def printResultFormatted(value, title, round=2):
    print("{:<5} {:<15}".format(f"{value:.2f}%", title))