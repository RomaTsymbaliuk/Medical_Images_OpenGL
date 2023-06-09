import pydicom
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *


def name_axis(x, y, z, text):
    glColor3f(1, 1, 1)
    glRasterPos3f(x, y, z)
    for c in text:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ctypes.c_int(ord(c)))


def draw_axis():
    glColor3f(1, 1, 1)
    glBegin(GL_LINES)
    glVertex3f(-2.0, 0.0, 0.0)
    glVertex3f(2.0, 0.0, 0.0)
    glVertex3f(0.0, -2.0, 0.0)
    glVertex3f(0.0, 2.0, 0.0)
    glVertex3f(0.0, 0.0, -2.0)
    glVertex3f(0.0, 0.0, 2.0)
    glEnd()
    name_axis(1.2, 0, 0, "x")
    name_axis(0, 1.2, 0, "y")
    name_axis(0, 0, 0.9, "z")


def tex_image_set_up(height, width, pixel_array, t):
    glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, height, width, 0, GL_LUMINANCE, GL_UNSIGNED_BYTE,
                 pixel_array[t])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)


def z_move_set_up():
    glBegin(GL_QUADS)
    z_position = dicom.t1 * (dicom.slice_thickness + dicom.space_between_slices) / dicom.height
    glTexCoord2f(0, 0)
    glVertex3f(0, 0, z_position)
    glTexCoord2f(1, 0)
    glVertex3f(1, 0, z_position)
    glTexCoord2f(1, 1)
    glVertex3f(1, 1, z_position)
    glTexCoord2f(0, 1)
    glVertex3f(0, 1, z_position)
    glEnd()


def x_move_set_up(z_vertex):
    glBegin(GL_QUADS)
    x_position = dicom.t2 / dicom.height
    glTexCoord2f(0, 0)
    glVertex3f(x_position, 0, 0)
    glTexCoord2f(1, 0)
    glVertex3f(x_position, 1, 0)
    glTexCoord2f(1, dicom.n / 32)
    glVertex3f(x_position, 1, z_vertex)
    glTexCoord2f(0, dicom.n / 32)
    glVertex3f(x_position, 0, z_vertex)
    glEnd()


def y_move_set_up(z_vertex):
    glBegin(GL_QUADS)
    y_position = dicom.t3 / dicom.height
    glTexCoord2f(0, 0)
    glVertex3f(0, y_position, 0)
    glTexCoord2f(1, 0)
    glVertex3f(1, y_position, 0)
    glTexCoord2f(1, dicom.n / 32)
    glVertex3f(1, y_position, z_vertex)
    glTexCoord2f(0, dicom.n / 32)
    glVertex3f(0, y_position, z_vertex)
    glEnd()


def create_texture():
    z_vertex_3f = dicom.n * (dicom.slice_thickness + dicom.space_between_slices) / dicom.height
    glEnable(GL_TEXTURE_2D)
    #set up z
    tex_image_set_up(dicom.height, dicom.width, dicom.image_pixels, dicom.t1)
    z_move_set_up()
    # set up x
    tex_image_set_up(dicom.height, 32, dicom.side_pixels, dicom.t2)
    x_move_set_up(z_vertex_3f)
    # set up y
    tex_image_set_up(dicom.width, 32, dicom.front_pixels, dicom.t3)
    y_move_set_up(z_vertex_3f)
    glDisable(GL_TEXTURE_2D)
    glFlush()


def display_all():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glPushMatrix()
    glRotatef(-60, 1, 0, 0)
    glRotatef(-45, 0, 0, 1)  # Змінено напрям повороту
    draw_axis()
    create_texture()
    glPopMatrix()
    glutSwapBuffers()


def reflection_about_the_origin():
    return np.array([[-1, 0, 0, 0],
                    [0, -1, 0, 0],
                    [0, 0, -1, 0],
                    [0, 0, 0, 1]], dtype=float)


def actions(key, x, y):
    if key == b'r':
        matrix = reflection_about_the_origin()
        glMultMatrixf(matrix)
    # moving along Oz
    elif key == b'w' and dicom.t1 < dicom.n - 1:
        dicom.t1 += 1
    elif key == b's' and dicom.t1 > 0:
        dicom.t1 -= 1
    # moving along Ox
    elif key == b'd' and dicom.t2 < dicom.width - 1:
        dicom.t2 += 1
    elif key == b'a' and dicom.t2 > 0:
        dicom.t2 -= 1
    # moving along Oy
    elif key == b'q' and dicom.t3 < dicom.height - 1:
        dicom.t3 += 1
    elif key == b'e' and dicom.t3 > 0:
        dicom.t3 -= 1
    display_all()


class BrainImageDicom:
    def __init__(self, path, first_name):
        self.n = 20
        first_dicom = pydicom.read_file(path + first_name)
        self.height = first_dicom['0028', '0010'].value
        self.width = first_dicom['0028', '0011'].value
        self.slice_thickness = first_dicom['0018', '0050'].value
        self.space_between_slices = first_dicom['0018', '0088'].value
        self.intercept = first_dicom['0028', '1052'].value
        self.slope = first_dicom['0028', '1053'].value
        # set image type
        if self.intercept != 0 and self.slope != 1:
            self.image_type = np.dtype('float')
        else:
            self.image_type = np.dtype('int' + str(first_dicom['0028', '0100'].value))

        self.max_brightness = np.iinfo(self.image_type).max

        self.image_pixels = np.zeros((self.n, self.height, self.width))
        self.front_pixels = np.zeros((self.height, self.n + 12, self.width))
        self.side_pixels = np.zeros((self.width, self.n + 12, self.height))
        self.image_pixels = []

        for i in range(1, self.n + 1):
            current_image = pydicom.read_file(self.get_file_name(path, i))
            self.image_pixels.append(self.normalization(current_image.pixel_array))

        for i in range(self.height):
            for j in range(self.n):
                for k in range(self.width):
                    self.front_pixels[i][j][k] = self.image_pixels[j][i][k]
        for i in range(self.width):
            for j in range(self.n):
                for k in range(self.height):
                    self.side_pixels[i][j][k] = self.image_pixels[j][k][i]
        self.t1 = 0
        self.t2 = 0
        self.t3 = 0

    def get_file_name(self, path, i):
        return "{0}brain_0{1}{2}.dcm".format(path, "0" if i < (self.n // 2) else "", str(i))

    def normalization(self, pixels):
        min_new = 0
        max_new = 255
        min_peak = np.min(pixels)
        max_peak = np.max(pixels)
        normal = min_new + ((pixels - min_peak) / (max_peak - min_peak)) * (max_new - min_new)
        return normal.astype('uint8')


def main():
    global dicom
    # 16-bit images set
    file_path = "./"
    first_name = "brain_001.dcm"

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    dicom = BrainImageDicom(file_path, first_name)
    # window must be twice bigger
    glutInitWindowSize(2 * dicom.width, 2 * dicom.height)
    glutInitWindowPosition(500, 100)
    glutCreateWindow('Tsymbaliuk Lab 7')

    glEnable(GL_TEXTURE_2D)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_MODELVIEW)
    glRotatef(-60, 1, 0, 0)
    glRotatef(45, 0, 0, 1)
    glutDisplayFunc(display_all)
    glutKeyboardFunc(actions)
    glutMainLoop()

main()

