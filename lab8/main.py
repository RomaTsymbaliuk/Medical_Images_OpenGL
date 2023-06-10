import pydicom
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

def alpha_compositing(layer1, layer2, alpha):
    result = []
    for row1, row2 in zip(layer1, layer2):
        new_row = []
        for pixel1, pixel2 in zip(row1, row2):
            new_pixel = [pixel1[0] * alpha + pixel2[0] * (1 - alpha),
                         pixel1[1] * alpha + pixel2[1] * (1 - alpha),
                         pixel1[2] * alpha + pixel2[2] * (1 - alpha)]
            new_row.append(new_pixel)
        result.append(new_row)
    return result

def pixels_to_rgb(dicom):
    pixels_to_show = []
    for row in dicom.pixels:
        new_row = []
        for value in row:
            if 'r' == None:
                new_row.append([value, 0, 0])
            elif 'g' == None:
                new_row.append([0, value, 0])
            elif 'b' == None:
                new_row.append([0, 0, value])
            else:
                new_row.append([value, value, value])
        pixels_to_show.append(new_row)
    return pixels_to_show

def actions(key, x, y):
    global current_pixels
    if key == b'c':
        current_pixels = pixels_to_rgb(dicom_ct)
    if key == b'm':
        current_pixels = pixels_to_rgb(dicom_mri)
    if key == b'x':
        alpha = 0.5
        current_pixels = alpha_compositing(pixels_to_rgb(dicom_ct), pixels_to_rgb(dicom_mri), alpha)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, dicom_ct.width, dicom_ct.height, 0, type, GL_UNSIGNED_BYTE, current_pixels)

    show_image()

def create_texture(pixels, type):
    glBindTexture(GL_TEXTURE_2D, glGenTextures(1))
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, dicom_ct.width, dicom_ct.height, 0, type, GL_UNSIGNED_BYTE, pixels)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

def reshape(w, h):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glViewport(0, 0, w, h)
    gluOrtho2D(-w / 2, w / 2, -h / 2, h / 2)

def show_image():
    glClearColor(0.0, 0.0, 0.0, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glBegin(GL_QUADS)
    glTexCoord(1.0, 1.0)
    glVertex(-dicom_mri.width / 2, -dicom_mri.height / 2)
    glTexCoord(0.0, 1.0)
    glVertex(dicom_mri.width / 2, -dicom_mri.height / 2)
    glTexCoord(0.0, 0.0)
    glVertex(dicom_mri.width / 2, dicom_mri.height / 2)
    glTexCoord(1.0, 0.0)
    glVertex(-dicom_mri.width / 2, dicom_mri.height / 2)
    glEnd()
    glFlush()

class BrainImageDicom:
    def __init__(self, path, file_name):
        self.image = pydicom.read_file(path + file_name)
        self.height = self.image['0028', '0010'].value
        self.width = self.image['0028', '0011'].value
        self.image_type = np.dtype('int' + str(self.image['0028', '0100'].value))
        self.max_brightness = np.iinfo(self.image_type).max
        self.pixels = self.image.pixel_array

def main():
    global dicom_ct, dicom_mri
    # 8-bit images
    file_path = "./"
    file_name_ct = "2-ct.dcm"
    file_name_mri = "2-mri.dcm"
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    dicom_ct = BrainImageDicom(file_path, file_name_ct)
    dicom_mri = BrainImageDicom(file_path, file_name_mri)
    glutInitWindowSize(dicom_mri.width, dicom_mri.height)
    glutInitWindowPosition(500, 100)
    glutCreateWindow('Tsymbaliuk Lab 8')
    create_texture(pixels_to_rgb(dicom_ct), GL_RGB)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glutDisplayFunc(show_image)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(actions)
    glutMainLoop()

main()
