import numpy as np
import cv2
import os
import argparse
import datetime
import errno
import math

DEG_TO_RAD = math.pi / 180
MAX = 255
BLUR = 9
IM_SCALE = 0.80

def processFile(file, num_scans, tresh):
    global IMAGES, SCANS
    global NUM_SCANS
    NUM_SCANS = int(num_scans)

    img = openImage(file)
    scans = findScans(img, int(tresh))
    
    # Vytvoření složky 'CROPED' ve stejném adresáři jako vstupní soubor
    output_dir = os.path.join(os.path.dirname(file), 'CROPED')
    os.makedirs(output_dir, exist_ok=True)  # Vytvoří složku, pokud neexistuje

    savedfiles = writeScans(output_dir, file, scans)  # Předání cesty k výstupní složce
    IMAGES += 1
    SCANS += len(scans)
    print(savedfiles)
    return savedfiles

ERRORS = 0  # Celkový počet chyb
IMAGES = 0  # Celkový počet zpracovaných obrázků
SCANS = 0   # Celkový počet nalezených skenů

def openImage(file):
    img = cv2.imread(file)
    if img is None:
        print("Error: Failed to open image at path: " + file)
        global ERRORS
        ERRORS += 1
    return img

def writeImage(fileName, img):
    success = cv2.imwrite(fileName, img)
    if not success:
        print("Error: Failed to write image " + fileName + " to file.")
        global ERRORS
        ERRORS += 1
        return False
    return True

def writeScans(output_dir, original_file_name, scans):
    if len(scans) == 0:
        print("Warning: No scans were found in this image: " + original_file_name)
        global ERRORS
        ERRORS += 1
        return

    name, ext = os.path.splitext(os.path.basename(original_file_name))
    num = 0
    files = []
    for item in scans:
        f = os.path.join(output_dir, "{}_{}{}".format(name, num, ext))  # Uložení do složky 'CROPED'
        writeImage(f, item)
        files.append(f)
        num += 1
    return files

def getAveROISize(candidates):
    if len(candidates) == 0:
        return 0
    av = 0
    for roi in candidates:
        av += cv2.contourArea(roi[0])
    return av / len(candidates)

def getROI(contours):
    roi = []
    for contour in contours:
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        roi.append([box, rect])
    roi = sorted(roi, key=lambda b: cv2.contourArea(b[0]), reverse=True)
    candidates = []
    for b in roi:
        if len(candidates) >= NUM_SCANS:
            break
        candidates.append(b)
    return candidates

def rotateImage(img, angle, center):
    (h, w) = img.shape[:2]
    mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, mat, (w, h), flags=cv2.INTER_LINEAR)

def rotateBox(box, angle, center):
    rad = -angle * DEG_TO_RAD
    sine = math.sin(rad)
    cosine = math.cos(rad)
    rotBox = []
    for p in box:
        p[0] -= center[0]
        p[1] -= center[1]
        rot_x = p[0] * cosine - p[1] * sine
        rot_y = p[0] * sine + p[1] * cosine
        p[0] = rot_x + center[0]
        p[1] = rot_y + center[1]
        rotBox.append(p)
    return np.array(rotBox)

def getCenter(box):
    x_vals = [i[0] for i in box]
    y_vals = [i[1] for i in box]
    cen_x = (max(x_vals) + min(x_vals)) / 2
    cen_y = (max(y_vals) + min(y_vals)) / 2
    return (cen_x, cen_y)

def clipScans(img, candidates):
    scans = []
    for roi in candidates:
        rect = roi[1]
        box = np.int0(roi[0])
        angle = rect[2]
        if angle < -45:
            angle += 90
        center = getCenter(box)
        rotIm = rotateImage(img, angle, center)
        rotBox = rotateBox(box, angle, center)
        x_vals = [i[0] for i in rotBox]
        y_vals = [i[1] for i in rotBox]
        try:
            scans.append(rotIm[min(y_vals):max(y_vals), min(x_vals):max(x_vals)])
        except IndexError as e:
            print("Error: Rotated image is out of bounds!\n" +
                  "Try straightening the picture, and moving it away from the scanner's edge.", e)
            global ERRORS
            ERRORS += 1
    return scans

def findScans(img, tresh):
    blur = cv2.medianBlur(img, BLUR)
    grey = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    _, thr = cv2.threshold(grey, tresh, MAX, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    roi = getROI(contours)
    scans = clipScans(img, roi)
    return scans

if __name__ == '__main__':
    print('local run')
    inputfiles = ['/Users/mac/Desktop/20250108170921_00001.jpg']
    output = processFile(str(inputfiles[0]), 20, 220)
