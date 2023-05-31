import sys
import pydicom
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays.numpymodule import ARRAY_TO_GL_TYPE_MAPPING


def initialize():
    global dicom
    create_texture(dicom.pixel_array, GL_LUMINANCE)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 0.0)

def upload_dicom(file_name):
    global dicom, height, width
    dicom = pydicom.read_file(file_name)
    height = dicom['0028', '0010'].value
    width = dicom['0028', '0011'].value

def create_texture(pixels, type):
    gl_type = ARRAY_TO_GL_TYPE_MAPPING.get(pixels.dtype)
    glBindTexture(GL_TEXTURE_2D, glGenTextures(1))
    glTexImage2D(GL_TEXTURE_2D, 0, type, width, height, 0, type, gl_type, pixels)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

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

def reshape(w, h):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluOrtho2D(0.0, w, 0.0, h)

def create_gradient_with_LUT(pixels):
    lut = np.linspace(0, 255, 256, dtype=np.uint8)
    result = []
    for pixel_list in pixels:
        row = []
        for pixel in pixel_list:
            row.append(lut[pixel])
        result.append(row)

    return np.array(result)

def set_up_coloring(pixels):
    global height, width
    rgb = np.zeros((height, width, 3), 'uint8')
    # R - 0, G - 1, B - 2
    rgb[..., 0] = 0
    rgb[..., 1] = pixels
    rgb[..., 2] = 0
    return rgb

def create_mask():
    mask = np.hstack((
        np.full((height, width // 2), 255, dtype=np.uint8),
        np.zeros((height, width // 2), dtype=np.uint8)
    ))
    return mask

def set_up_mask(pixels):
    result = []
    bit_map = create_mask()
    for i, row in enumerate(pixels):
        new_row = []
        for j, pixel in enumerate(row):
            new_row.append(bit_map[i][j] & pixel)
        result.append(new_row)
    return np.array(result, np.uint8)

def actions(key, x, y):
    global dicom
    if key == b'1':
        new_values = set_up_coloring(create_gradient_with_LUT(np.array(dicom.pixel_array)))
        create_texture(new_values, GL_RGB)
        show_image()
    elif key == b'2':
        new_values = set_up_mask(np.array(dicom.pixel_array))
        create_texture(new_values, GL_LUMINANCE)
        show_image()
    elif key == b'0':
        create_texture(dicom.pixel_array, GL_LUMINANCE)
        show_image()

file_path = "./"
file_name = "DICOM_Image_8b.dcm"
glutInit('')
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
upload_dicom(file_path + file_name)
glutInitWindowSize(width, height)
glutInitWindowPosition(100, 50)
glutCreateWindow('Tsymbaliuk Lab 1')
initialize()
glutDisplayFunc(show_image)
glutReshapeFunc(reshape)
glutKeyboardFunc(actions)
glutMainLoop()
