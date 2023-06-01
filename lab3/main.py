import pydicom
import copy
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays.numpymodule import ARRAY_TO_GL_TYPE_MAPPING
import math

MIN = 0.35
MAX = 0.85

mask_high_filter = [[-1, -1, -1],
                    [-1,  9, -1],
                    [-1, -1, -1]]


isotropic_filter_x = [[-1, 0, 1],
                    [-math.sqrt(2), 0, math.sqrt(2)],
                    [-1, 0, 1]]

isotropic_filter_y = [[-1, -math.sqrt(2), -1],
                      [0, 0, 0],
                      [1, math.sqrt(2), 1]]


def min_max_pixels(pixels):
    pixels_array = []
    for row in pixels:
        for pixel in row:
            pixels_array.append(pixel)
    return {'min': min(pixels_array), 'max': max(pixels_array)}

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
            new_value = min_new + ((value-min_peak)/(max_peak-min_peak))*(max_new-min_new)
            new_row.append(int(new_value))
        new_pixels.append(new_row)
    return np.array(new_pixels, image_type)

def pixel_distribution(pixels, mask, i, j):
    global height, width
    mask_copy = copy.deepcopy(mask)
    pixel_value = 0

    for k in range(-1, 2):
        for n in range(-1, 2):
            check_for_i = (i + k) < 0 or (i + k) > width - 1
            check_for_j = (j + n) < 0 or (j + n) > height - 1

            if check_for_i or check_for_j:
                #first column, (j + n) out of range
                if check_for_j and not check_for_i:
                    pixel_value += int(round(pixels[i + k][j + 3 * n] * mask_copy[k + 1][n + 1]))
                    break
                if check_for_i and not check_for_j:
                    pixel_value += int(round(pixels[i + 3 * k][j + n] * mask_copy[k + 1][n + 1]))
                    break
                if check_for_i and check_for_j:
                        pixel_value += int(round(pixels[i + 3 * k][j + 3 * n] * mask_copy[k + 1][n + 1]))
                        break
            else:
                pixel_value += int(round(pixels[i + k][j + n] * mask_copy[k + 1][n + 1]))

    return pixel_value

def high_frequency_filter(pixels, mask):
    global max_brightness
    result = []
    for i, row in enumerate(pixels):
        new_row = []
        for j, pixel in enumerate(row):
            pixel_value = pixel_distribution(pixels, mask, i, j)
            if pixel_value < 0:
                pixel_value = 0
            elif pixel_value > max_brightness:
                pixel_value = max_brightness
            new_row.append(pixel_value)

        result.append(new_row)
    return np.array(result, image_type)

def actions(key, x, y):
    mask_name = ''
    global dicom, current_pixels
    if key == b'h':
        current_pixels = high_frequency_filter(normalization(np.array(dicom.pixel_array)), mask_high_filter)
        mask_name = 'High frequency mask filter'
    elif key == b'w':
        mask_name = 'Mask W'
    elif key == b's':
        mask_name = 'Mask S'
    elif key == b'o':
        current_pixels = dicom.pixel_array
    create_texture(current_pixels, GL_LUMINANCE)
    show_image()

    info_text = mask_name + ' was set' if mask_name != '' else 'Original image'
    print(info_text)

def reshape(w, h):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluOrtho2D(0.0, w, 0.0, h)

def show_image():
    global width, height
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
    # return GL_SHORT
    gl_type = ARRAY_TO_GL_TYPE_MAPPING.get(pixels.dtype)
    glBindTexture(GL_TEXTURE_2D, glGenTextures(1))
    glTexImage2D(GL_TEXTURE_2D, 0, type, width, height, 0, type, gl_type, pixels)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

def initialization():
    global dicom
    create_texture(dicom.pixel_array, GL_LUMINANCE)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 0.0)


def upload_dicom(file_name):
    global width, height, dicom, current_pixels, max_brightness, image_type
    dicom = pydicom.read_file(file_name)
    current_pixels = dicom.pixel_array
    height = dicom['0028', '0010'].value
    width = dicom['0028', '0011'].value
    # set image type (int16)
    image_type = np.dtype('int' + str(dicom['0028', '0100'].value))
    # max value - int8
    max_brightness = np.iinfo(image_type).max

def main():
    # 16-bit image
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
    glutCreateWindow('Tsymbaliuk Lab 3')

    initialization()
    glutDisplayFunc(show_image)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(actions)
    glutMainLoop()

main()

