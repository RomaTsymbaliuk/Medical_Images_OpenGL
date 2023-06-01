import pydicom
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays.numpymodule import ARRAY_TO_GL_TYPE_MAPPING

max_brightness = 25
min_brightness = 0

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
    # max value - int16
    max_brightness = np.iinfo(image_type).max


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


def min_max_pixels(pixels):
    pixels_array = []
    for row in pixels:
        for pixel in row:
            pixels_array.append(pixel)
    return {'min': min(pixels_array), 'max': max(pixels_array)}


def binarization(pixels):
    min_max_dict = min_max_pixels(pixels)
    minn = min_max_dict["min"]
    maxx = min_max_dict["max"]
    threshold = 0.26
    new_pixels = []
    for row in pixels:
        new_row = []
        for pixel in row:
            if pixel < threshold * maxx:
                new_row.append(minn)
            else:
                new_row.append(maxx)
        new_pixels.append(new_row)

    return np.array(new_pixels)

def window_level_operation(pixels):
    level = ((max(map(max, pixels)) * 0.2) - (min(map(min, pixels)) * -0.2)) / 2
    window = ((max(map(max, pixels)) * 0.2) - (min(map(min, pixels)) * -0.2))
    min_value = level - window / 2
    max_value = level + window / 2

    output = np.clip(pixels, min_value, max_value)
    output = (output - min_value) / (max_value - min_value) * 255
    output = np.uint8(output)

    return np.array(output)

def actions(key, x, y):
    global dicom, current_pixels
    if key == b'w':
        current_pixels = window_level_operation(np.array(dicom.pixel_array))
    elif key == b'b':
        current_pixels = binarization(np.array(dicom.pixel_array))
    elif key == b'a':
        current_pixels = dicom.pixel_array
    create_texture(current_pixels, GL_LUMINANCE)
    show_image()


def show_text(text, x, y):
    glDisable(GL_TEXTURE_2D)
    glColor3f(255, 255, 255)
    glRasterPos2f(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(character))
    glEnable(GL_TEXTURE_2D)


def cursor_info_show(x, y):
    global current_pixels
    w = glutGet(GLUT_WINDOW_WIDTH)
    h = glutGet(GLUT_WINDOW_HEIGHT)
    # brightness must be shown only if user point on data
    if 0 < x < w and 0 < y < h:
        brightness = "Brightness: " + str(current_pixels[x][y]) 
        show_image()
        show_text(brightness, 5, h - 15)
    else:
        show_image()
    glFlush()

file_path = "./"
file_name = "DICOM_Image_8b.dcm"
glutInit(sys.argv)
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
upload_dicom(file_path + file_name)
glutInitWindowSize(width, height)
glutInitWindowPosition(100, 100)
glutCreateWindow("Tsymbaliuk Lab 2")

initialization()
glutDisplayFunc(show_image)
glutReshapeFunc(reshape)
glutKeyboardFunc(actions)
glutPassiveMotionFunc(cursor_info_show)
glutMainLoop()
