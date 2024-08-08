import rawpy
import numpy as np
import re
import math

RED = 0
GREEN_1 = 1
BLUE = 2
GREEN_2 = 3

# Supported raw types
RAW_FORMATS = {
    "PANASONIC": "RW2",
    "CANON": "CR2"
    }

# ------------------------
# - ACTIVATION FUNCTIONS -
# ------------------------

# Starts the raw processing for a single image
def processRawImage(image, channelToSeparate="g"):
    # Check for valid image type
    if not isinstance(image, rawpy.RawPy):
        raise Exception(" ! Input can't be processed. The images need to be raw files imported with rawpy.")
    
    # Check for valid color channel
    if not re.compile(r'^[rRgGbB]$').match(channelToSeparate):
        raise Exception(" ! '" + str(channelToSeparate) + "' is not a valid color channel. Use 'r', 'g' or 'b'.")
    
    imgNormalized = normalizeRawImage(image.raw_image_visible, image.raw_pattern, image.black_level_per_channel, image.camera_white_level_per_channel)
    imgDebayered = debayerSingleColor(imgNormalized, channelToSeparate)

    return imgDebayered

# Starts the raw processing for two images
def processRawImagePair(img1, img2, channelToSeparate="g"):
    img1_out = processRawImage(img1, channelToSeparate)
    img2_out = processRawImage(img2, channelToSeparate)
    return img1_out, img2_out

# -----------------
# - KEY FUNCTIONS -
# -----------------

# Normalize: Force BGGR, correct black- and whitelevel, Normalize (0-255)
def normalizeRawImage(rawImage, bayerpattern, blacklevel, whitelevel, type=np.uint8):
    # Convert image for BGGR bayerpattern
    if bayerpattern[0][0] == GREEN_1 or bayerpattern[0][0] == GREEN_2:
        if bayerpattern[0][1] == BLUE:
            print(" > Converting image from GBRG to BGGR")
            rawImage = rawImage[:, 1:-1]
        else:
            print(" > Converting image from GRBG to BGGR")
            rawImage = rawImage[1:-1]
    elif bayerpattern[0][0] == RED:
        print(" > Converting image from RGGB to BGGR")
        rawImage = rawImage[1:-1, 1:-1]

    print(" > Normalizing")
    blackR = blacklevel[RED]
    blackG = blacklevel[GREEN_1]
    blackB = blacklevel[BLUE]
    whiteR = whitelevel[RED] - blackR
    whiteG = whitelevel[GREEN_1] - blackG
    whiteB = whitelevel[BLUE] - blackB

    if blackR != blackG or blackB != blackR:
        normalizedImage = []
        for y, yVal in enumerate(rawImage):
            normalizedImage.append([])
            for x, xVal in enumerate(yVal):
                if (y % 2 == 0 and x % 2 == 1) or (y % 2 == 1 and x % 2 == 0):
                    # GREEN
                    normalizedImage[y].append(((xVal-blackG)/whiteG * 255).astype(type))
                elif (y % 2 == 0 and x % 2 == 0):
                    # BLUE
                    normalizedImage[y].append(((xVal-blackB)/whiteB * 255).astype(type))
                else:
                    # RED
                    normalizedImage[y].append(((xVal-blackR)/whiteR * 255).astype(type))
    else:
        rawImage[rawImage <= blackR] = blackR # Prevent underflowing
        normalizedImage = ((rawImage-blackR) / (whiteR) * 255).astype(type)

    return normalizedImage

# Does debayering for a single color of an rggb-image 
def debayerSingleColor(bggrImg, debayerChannel):
    bggrImg = np.array(bggrImg)
    imgHeight, imgWidth = bggrImg.shape[:2]

    if re.search('g', debayerChannel, re.IGNORECASE):
        # Green debayer
        newWidth = math.ceil((imgHeight + imgWidth)/2)
        newHeight = newWidth-1
        rotImage = np.zeros((newHeight, newWidth), dtype=np.uint8)
        for y in range(imgHeight):
                for x in range(imgWidth):
                    # If its a green pixel put it at the rotated location (BGGR)
                    if (y % 2 == 0 and x % 2 == 1) or (y % 2 == 1 and x % 2 == 0):
                        newY = math.ceil((y + x)/2)-1
                        newX = math.ceil((imgWidth - 1 - x + y)/2)
                        rotImage[newY][newX] = bggrImg[y][x]
        return rotImage
    else:
        # Red / blue debayer
        newHeight = math.ceil(imgHeight/2 + 1)
        newWidth = math.ceil(imgWidth/2 + 1)
        debayeredImage = np.zeros((newHeight, newWidth), dtype=np.uint8)

        isRedDebayer = re.search('r', debayerChannel, re.IGNORECASE)
        isBlueDebayer = re.search('b', debayerChannel, re.IGNORECASE)

        for y in range(imgHeight):
                for x in range(imgWidth):
                    # If its a red or blue pixel store it in the corresponding new image (BGGR)
                    if (isBlueDebayer and (y % 2 == 0 and x % 2 == 0)) or (isRedDebayer and (y % 2 == 1 and x % 2 == 1)):
                        newY = math.ceil((y)/2)
                        newX = math.ceil((x)/2)
                        debayeredImage[newY][newX] = bggrImg[y][x]
                        
        return debayeredImage


# Support function
def readRawImage(path, name, fileExtention):
    return rawpy.imread(path + name + "." + fileExtention)


