import pydicom 
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from math import *
from OpenGL.arrays.numpymodule import ARRAY_TO_GL_TYPE_MAPPING

MIN = 0.05
MAX = 0.95
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

def angle_shift_in_OY_direction(alpha, b):
    return np.array([[1, 0, 0, 0],
                      [np.tan(alpha), 1, 0, 0],
                      [0, 0, 1, -b * np.sin(alpha)],
                      [0, 0, 0, 1]], dtype=float)

def scaling_relative_to_given_point(Sy):
    return np.array([[1, 0, 0, 0],
                     [0, Sy, 0, 0],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]], dtype=float)

def actions(key, x, y):
    global pixels_normal, first, second, matrix
    glLoadMatrixf(def_matrix)
    if key == b't':
        alpha = 14
        Sy = 1 
        xp = 10
        yp = 10

        first = angle_shift_in_OY_direction(radians(alpha), b = 4)
        matrix = first.dot(np.array([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]], dtype=float))
        glMultMatrixf(matrix)
    if key == b'o':
        Sy = 2

        second = scaling_relative_to_given_point(Sy)
        matrix = second.dot(np.array([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]], dtype=float))
        glMultMatrixf(matrix)


def reshape(w, h):
    global def_matrix
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glViewport(0, 0, w, h)
    gluOrtho2D(-w / 2, w / 2, -h / 2, h / 2)
    def_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)

def show_image():
    global width, height
    glClearColor(0.0, 0.0, 0.0, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glBegin(GL_QUADS)
    half_value = width // 2
    glTexCoord3f(1.0, 0.0, 0.0)
    glVertex3f(half_value, -half_value, 0.0)
    glTexCoord3f(1.0, 1.0, 0.0)
    glVertex3f(-half_value, -half_value, 0.0)
    glTexCoord3f(0.0, 1.0, 0.0)
    glVertex3f(-half_value, half_value, 0.0)
    glTexCoord3f(0.0, 0.0, 0.0)
    glVertex3f(half_value, half_value, 0.0)
    glEnd()
    glFlush()

def create_texture(pixels, type):
    gl_type = ARRAY_TO_GL_TYPE_MAPPING.get(pixels.dtype)
    glBindTexture(GL_TEXTURE_2D, glGenTextures(1))
    glTexImage2D(GL_TEXTURE_2D, 0, type, width, height, 0, type, gl_type, pixels)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

def initialization():
    global pixels_original, pixels_normal
    pixels_original = dicom.pixel_array
    pixels_normal = normalization(np.array(dicom.pixel_array))

    create_texture(pixels_normal, GL_LUMINANCE)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 0.0)

def upload_dicom(file_name):
    global width, height, dicom, current_pixels, max_brightness, image_type
    dicom = pydicom.read_file(file_name)
    current_pixels = dicom.pixel_array
    height = dicom['0028', '0010'].value
    width = dicom['0028', '0011'].value
    intercept = dicom['0028', '1052'].value
    slope = dicom['0028', '1053'].value
    # set image type
    if intercept != 0 and slope != 1:
        image_type = np.dtype('float')
    else:
        image_type = np.dtype('int' + str(dicom['0028', '0100'].value))

    # max value
    max_brightness = np.iinfo(image_type).max

def main():
    # 16-bit image
    file_path = "./"
    file_name = "DICOM_Image_16b.dcm"
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    # upload image with file_name from path
    upload_dicom(file_path + file_name)
    # window must be twice bigger
    glutInitWindowSize(2 * width, 2 * height)
    # position on screen
    glutInitWindowPosition(500, 100)
    glutCreateWindow('Tsymbaliuk Lab 6')
    initialization()
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glutDisplayFunc(show_image)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(actions)
    glutMainLoop()

main()

