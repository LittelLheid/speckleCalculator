import numpy

PI = numpy.pi

# Calculates the focal length and f-number to choose for measuring speckle
def calcFNumAndFocalLength(wavelength, pixelWidth, fNumRange=(2.8, 22), focalLenghtRange=(12,60)):
    # Convert to meter
    wavelength /= 10**9 # expected in nanometer
    pixelWidth /= 10**6 # expected in micrometer
    clearAperture = 3.2*10**-3 # Clear aperture of the eye

    fNumMin, fNumMax = fNumRange
    focalLenghtMin, focalLenghtMax = focalLenghtRange
    pixelArea = pixelWidth**2 
 
    wantedSqrtRatio = 0.54
    wantedFnum = numpy.sqrt((PI*pixelArea)/(4*wantedSqrtRatio**2*wavelength**2))
    wantedFocalLength = numpy.sqrt((((clearAperture)**2)*PI*pixelArea)/(4*wantedSqrtRatio**2*wavelength**2))*10**3

    # Best possible values
    print("Wanted parameters:")
    print(" > f/" + str(round(wantedFnum, 1)))
    print(" > " + str(round(wantedFocalLength, 1)) + "mm")

    # Account for possible ranges of focal length and f-number
    allFNums = [1, 1.4, 2, 2.8, 4, 5.6, 8, 11, 16, 22, 32, 45]
    possibleFnums = []
    for fNum in allFNums:
        if fNum >= fNumMin and fNum <= fNumMax:
            possibleFnums.append(fNum)
        else: 
            possibleFnums.append(fNumMin)
    if focalLenghtMin == focalLenghtMax:
        possibleFocalLengths = [focalLenghtMin]
    else:
        possibleFocalLengths = numpy.arange(focalLenghtMin, focalLenghtMax+1)
        
    bestFnum = min(possibleFnums, key=lambda fnum:abs(fnum-wantedFnum))

    newSpeckleArea = (4*wavelength**2*(bestFnum)**2)/PI
    newSqrtRatio = numpy.sqrt(pixelArea/newSpeckleArea)
    pixSpeckRatio = pixelArea/newSpeckleArea

    recalibratedFocalLength = numpy.sqrt((((clearAperture)**2)*PI*pixelArea)/(4*newSqrtRatio**2*wavelength**2))*10**3 # in mm
    bestFocalLength = min(possibleFocalLengths, key=lambda focLen:abs(focLen-recalibratedFocalLength)) # in mm

    newClearAperture = clearAperture
    if abs(recalibratedFocalLength-bestFocalLength) != 0: 
        newClearAperture = numpy.sqrt(((bestFocalLength*10**-3)**2*4*newSqrtRatio**2*wavelength**2)/(PI*pixelArea)) # in m

    # Best values that can be choosen with the camera
    print("\nChoose parameters:")
    print(" > f/" + str(round(bestFnum, 1)))
    print(" > " + str(round(bestFocalLength, 1)) + "mm")

    # Influence of the deviation from the best-case
    print("\nResulting influence: ")
    print("> sqrt ratio changed from " + str(round(wantedSqrtRatio, 2)) + " to " + str(round(newSqrtRatio, 2)))
    print(" > 'Speckle per pixel': " + str(round(pixSpeckRatio,2)))
    print("> clear aperture changed from " + str(round(clearAperture*10**3, 2)) + "mm to " + str(round(newClearAperture*10**3, 2)) + "mm")  
    print(" > for matching the human eye, the aperture diameter should lie between 3-4mm")
    print("> angular resolution " + str(round(numpy.degrees((1.22*wavelength)/(newClearAperture)), 4)) + "°")