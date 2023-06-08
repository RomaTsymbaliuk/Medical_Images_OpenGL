import pydicom
import numpy as np
from math import log
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays.numpymodule import ARRAY_TO_GL_TYPE_MAPPING

MIN = 0.0
MAX = 1.0

def min_max_pixels(pixels):
    pixels_array = []
    for row in pixels:
        for pixel in row:
            pixels_array.append(pixel)
    return {'min': min(pixels_array), 'max': max(pixels_array)}

# by default make normalization
def normalization(pixels):
    global max_brightness
    new_pixels = []
    min_max = min_max_pixels(pixels)
    min_new = 0
    max_new = max_brightness
    min_peak = min_max['min'] * MIN
    max_peak = min_max['max'] * MAX

    for row in pixels:
        new_row = []
        for value in row:
            new_value = min_new + ((value - min_peak) / (max_peak - min_peak)) * (max_new - min_new)
            new_row.append(int(new_value))
        new_pixels.append(new_row)
    return np.array(new_pixels, image_type)

def find_overlay_data(pixels):
    global max_brightness
    print(max_brightness)
    hist = np.zeros(max_brightness+1)
    for row in pixels:
        for value in row:
            if value > max_brightness:
                value = max_brightness
            hist[value] = hist[value] + 1
    # normalized histogram
    for i in range(len(hist)):
        hist[i] = hist[i] / pixels.size

    pT = np.zeros(hist.size)
    pT[0] = hist[0]
    for i in range(1, hist.size):
        pT[i] = pT[i - 1] + hist[i]

    epsilon = sys.float_info.min
    hB = np.zeros(hist.size)
    hW = np.zeros(hist.size)
    for t in range(0, hist.size):
        if pT[t] > epsilon:
            hhB = 0
            for i in range(0, t):
                if hist[i] > epsilon:
                    value_hhB = hist[i] / pT[t]
                    if value_hhB != 0:
                        hhB -= value_hhB * log(value_hhB)

            hB[t] = hhB

        pTW = 1 - pT[t]
        if pTW > epsilon:
            hhW = 0
            for i in range(t + 1, hist.size):
                if hist[i] > epsilon:
                    value_hhW = hist[i] / pTW
                    if value_hhW != 0:
                        hhW -= value_hhW * log(value_hhW)

            hW[t] = hhW

    jMax = hB[0] + hW[0]
    for t in range(1, hist.size):
        j = hB[t] + hW[t]
        if j > jMax:
            jMax = j

    return jMax

def adams_growing(pixels):
    global max_brightness
    new_pixels = []
    overlay = find_overlay_data(pixels)

    for row in pixels:
        new_row = []
        for value in row:
            if value <= overlay:
                new_value = 0
            else:
                new_value = max_brightness
            new_row.append(int(new_value))
        new_pixels.append(new_row)
    return np.array(new_pixels, image_type)

def create_property_table(pixels):
    global height, width, property_table
    property_table = np.zeros((height, width, 3), 'int16')
    adams_growing_pixels = adams_growing(pixels)
    property_table[..., 0] = pixels
    property_table[..., 1] = adams_growing_pixels
    property_table[..., 2] = pixels_normal

def make_texture_colored():
    global height, width
    rgb = np.zeros((height, width, 3), 'uint8')
    # R - 0, G - 1, B - 2
    rgb[..., 0] = 0
    rgb[..., 1] = property_table[..., 1]
    rgb[..., 2] = property_table[..., 2]
    return rgb

def actions(key, x, y):
    global isAlgorithmWorked
    if key == b'k':
        if not isAlgorithmWorked:
            create_property_table(pixels_original)
            isAlgorithmWorked = True
        create_texture(make_texture_colored(), GL_RGB)
        show_image()
        print('K')
    elif key == b'o':
        create_texture(pixels_normal, GL_LUMINANCE)
        show_image()

def reshape(w, h):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluOrtho2D(0.0, w, 0.0, h)


def show_image():
    glClear(GL_COLOR_BUFFER_BIT)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0.0, 0.0)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(0.0, width)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(height, width)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(height, 0.0)
    glEnd()
    glFlush()

def create_texture(pixels, type):
    gl_type = ARRAY_TO_GL_TYPE_MAPPING.get(pixels.dtype)
    glBindTexture(GL_TEXTURE_2D, glGenTextures(1))
    glTexImage2D(GL_TEXTURE_2D, 0, type, width, height, 0, type, gl_type, pixels)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

def initialization():
    global pixels_original, pixels_normal, isAlgorithmWorked
    isAlgorithmWorked = False
    pixels_original = dicom.pixel_array
    pixels_normal = normalization(np.array(dicom.pixel_array))

    create_texture(pixels_normal, GL_LUMINANCE)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 0.0)

def upload_dicom(file_name):
    global width, height, dicom, image_type, max_brightness
    dicom = pydicom.read_file(file_name)
    height = dicom['0028', '0010'].value
    width = dicom['0028', '0011'].value
    # set image type (int16)
    image_type = np.dtype('int' + str(dicom['0028', '0100'].value))
    # max value - int8
    max_brightness = np.iinfo(image_type).max

file_path = "./"
file_name = "DICOM_Image_8b.dcm"

glutInit(sys.argv)
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
# upload image with file_name from path
upload_dicom(file_path + file_name)
# set up image sizes
glutInitWindowSize(width, height)
# position on screen
glutInitWindowPosition(100, 100)
glutCreateWindow('Tsymbaliuk Lab 4')
initialization()
glutDisplayFunc(show_image)
glutReshapeFunc(reshape)
glutKeyboardFunc(actions)
glutMainLoop()
