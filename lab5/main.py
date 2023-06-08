import pydicom
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

def loadImageInWindow(width, height, Pixels, Type, model):
    glTexImage2D(GL_TEXTURE_2D, 0, model, width, height, 0, model, Type, Pixels)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glEnable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glTexCoord2d(0.0, 0.0)
    glVertex2d(0.0, 0.0)
    glTexCoord2d(1.0, 0.0)
    glVertex2d(width, 0.0)
    glTexCoord2d(1.0, 1.0)
    glVertex2d(width, height)
    glTexCoord2d(0.0, 1.0)
    glVertex2d(0.0, height)
    glEnd()
    glDisable(GL_TEXTURE_2D)

def getImageType():
    if dicom_source[0x0028, 0x1052].value != 0 and dicom_source[0x0028, 0x1053].value != 1:
        bTypeGl = GL_FLOAT
    else:
        if dicom_source[0x28, 0x101].value == 8:
            bTypeGl = GL_BYTE
        elif dicom_source[0x28, 0x101].value == 16:
            bTypeGl = GL_SHORT
    return bTypeGl

def displayCallback():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1, 1, 1)
    loadImageInWindow(width, height, normalizedPA(np.array(PixelArray)), getImageType(), GL_LUMINANCE)

def normalizedPA(pixels):
    level = ((max(map(max, pixels))) - 0) / 2
    window = ((max(map(max, pixels))) - 0)
    norm_PixelArray = [[min_brightness if j <= level - window / 2 else
                        max_brightness if j > level + window / 2 else
                        min_brightness + (j - level + (window / 2)) * (max_brightness - min_brightness) / window
                        for j in i]
                       for i in pixels]
    return np.array(norm_PixelArray, image_type)

def edgesMarrHildreth(img, sigma):
    size = int(2 * (np.ceil(3 * sigma)) + 1)
    x, y = np.meshgrid(np.arange(-size / 2 + 1, size / 2 + 1),
                       np.arange(-size / 2 + 1, size / 2 + 1))

    normal = 1 / (2.0 * np.pi * sigma**2)
    kernel = ((x**2 + y**2 - (2.0*sigma**2)) / sigma**4) * \
        np.exp(-(x**2+y**2) / (2.0*sigma**2)) / normal

    kern_size = kernel.shape[0]
    log = np.zeros_like(img, dtype=float)
    for i in range(img.shape[0]-(kern_size-1)):
        for j in range(img.shape[1]-(kern_size-1)):
            window = img[i:i+kern_size, j:j+kern_size] * kernel
            log[i, j] = np.sum(window)

    log = log.astype(np.int64, copy=False)
    zero_crossing = np.zeros_like(log)
    for i in range(1, log.shape[0] - 1):
        for j in range(1, log.shape[1] - 1):
            if log[i][j] == 0:
                if (log[i][j - 1] < 0 and log[i][j + 1] > 0) or (
                        log[i][j - 1] < 0 and log[i][j + 1] < 0) or (
                        log[i - 1][j] < 0 and log[i + 1][j] > 0) or (
                        log[i - 1][j] > 0 and log[i + 1][j] < 0):
                    zero_crossing[i][j] = max_brightness
            if log[i][j] < 0:
                if (log[i][j - 1] > 0) or (log[i][j + 1] > 0) or (log[i - 1][j] > 0) or (log[i + 1][j] > 0):
                    zero_crossing[i][j] = max_brightness

    return log, zero_crossing

def manipulation(bkey, x, y):
    key = bkey.decode("utf-8")
    norm_PixelArray = normalizedPA(np.array(PixelArray))

    if key == '1':
        displayCallback()
    elif key == '2':
        cur_pixel_log, thr = edgesMarrHildreth(norm_PixelArray, 0.565)
        norm_thr = normalizedPA(np.array(thr))
        loadImageInWindow(width, height, norm_thr, getImageType(), GL_LUMINANCE)
    glutSwapBuffers()

def UpdateWindow(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

def createWindow():
    glutInit(sys.argv)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(name)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glClearColor(0, 0, 0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

dicom_source = pydicom.read_file("./DICOM_Image_16b.dcm")
image_type = np.dtype('int' + str(dicom_source['0028', '0100'].value))
name = "Marr-Hildreth"
width = dicom_source[0x28, 0x10].value
height = dicom_source[0x28, 0x11].value
PixelArray = dicom_source.pixel_array
max_brightness = np.iinfo(image_type).max
min_brightness = 0
createWindow()
glutReshapeFunc(UpdateWindow)
glutKeyboardFunc(manipulation)
glutDisplayFunc(displayCallback)
glutMainLoop()
