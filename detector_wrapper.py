import cv2 as cv
import numpy as np


def canny(img):
    img_cvt = np.uint8(img)
    canny_img = cv.Canny(img_cvt, 50, 150, 3)
    return canny_img


def sobel(img):
    img = cv.blur(img, (9, 9))
    grad_x = cv.Sobel(img, cv.CV_16S, 1, 0, ksize=3, scale=1, delta=0, borderType=cv.BORDER_DEFAULT)
    grad_y = cv.Sobel(img, cv.CV_16S, 0, 1, ksize=3, scale=1, delta=0, borderType=cv.BORDER_DEFAULT)
    abs_grad_x = cv.convertScaleAbs(grad_x)
    abs_grad_y = cv.convertScaleAbs(grad_y)

    grad = cv.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
    grad = np.uint8(grad)
    return grad


def laplace(img):
    img = cv.blur(img, (15, 15))
    img = cv.blur(img, (15, 15))
    img = cv.blur(img, (15, 15))
    edge = cv.Laplacian(img, -1, 1)
    edge = edge / np.max(edge) * 255
    return edge


def usp(img):
    blur_img = cv.blur(img, (15, 15))
    return img - blur_img

