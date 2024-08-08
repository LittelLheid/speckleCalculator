from speckleCalculator import analyzeImage, analyzeSingleMeasurement, analyzeMeasurementBatch
from cameraSettingCalculator import calcFNumAndFocalLength
from rawProcessor import RAW_FORMATS
import os

scriptDir = os.path.dirname(__file__)
path = scriptDir + "\\img\\dataset1\\"

'''
Format of single measurement to be used with analyzeSingleMeasurement(MEASUREMENT) 
or as an array of multiple measurements with analyzeMeasurementBatch(ARRAY_OF_MEASUREMENTS).
measurement = {
        "path": "PATH TO IMAGE",
        "refName": "NAME_OF_REF",   // w/o datatype
        "imgName": "NAME_OF_SPECK",     // w/o datatype
        "datatype": "RW2",  // currently implemented: RW2, CR2, JPG/PNG
        "useRefImg": True,  // disable if no reference is used
        "debayerChannel": "g",  // channel to debayer as one letter string
        "saveFileName": "FILE TO SAVE CSV WITH RESULTS TO",     // leave empty if unwanted
        "metadata": {
                "distance": 1.2, // in m
                "fLen": 18,
                "aperture": 11.0,
                "iso": 800,
                "shutter": 1/20,
                "projInFocus": False,   // was the projector in focus during the specklemeasurement? 
                "camera": "LUMIX G7"    // used camera model used
        }
    }
'''

# Example of analyzeSingleMeasurement() and analyzeMeasurementBatch()
measurement = {
        "path": path,
        "refName": "06-09-green-01-ref",   
        "imgName": "06-09-green-01-speck",    
        "datatype": "RW2",  
        "useRefImg": True,  
        "debayerChannel": "g",  
        "saveFileName": "",  # Do not save results
        "metadata": {
                "distance": 1.2,
                "fLen": 18,
                "aperture": 11.0,
                "iso": 800,
                "shutter": 1/20,
                "projInFocus": False,  
                "camera": "LUMIX G7"   
        }}

analyzeSingleMeasurement(measurement)
# analyzeMeasurementBatch([measurement, measurement])


# Example for manual usage of analyzeImage()
analyzeImage(path, "06-09-red-01-ref", "06-09-red-01-speck", RAW_FORMATS["PANASONIC"], debayerChannel="r",
             metadata={"aperture": 11.0, "fLen": 18,"shutter": 0.1, "iso": 800, "distance": 1.0, "projInFocus": False, "camera": "LUMIX G7"})
analyzeImage(path, "06-09-green-01-ref", "06-09-green-01-speck", RAW_FORMATS["PANASONIC"], debayerChannel="g", 
             metadata={"aperture": 11.0, "fLen": 18,"shutter": 0.05, "iso": 800, "distance": 1.0, "projInFocus": False, "camera": "LUMIX G7"})
analyzeImage(path, "06-09-blue-01-ref", "06-09-blue-01-speck", RAW_FORMATS["PANASONIC"], debayerChannel="b",
             metadata={"aperture": 11.0, "fLen": 18,"shutter": 0.1, "iso": 800, "distance": 1.0, "projInFocus": False, "camera": "LUMIX G7"})

# Example of calcFNumAndFocalLength()
wavelength = 550
cameraPixelWidth = 3.75 # in micrometer
cameraApertureRange = (2.8, 22)
cameraFocalLengthRange = (12, 60)
calcFNumAndFocalLength(wavelength, cameraPixelWidth, cameraApertureRange, cameraFocalLengthRange) # LUMIX G7 with 12-60mm, f/2.8-f/22