import cv2 as cv
import numpy as np
import os
import matplotlib.pyplot as plt
import math
from detector_wrapper import canny, sobel, laplace, usp

IMG_NAME = ['test1.tif', 'test2.png', 'test3.jpg',
            'test4.bmp', 'test5.png','test6.jpg']
RES_DIR = './res/'

OUTPUT_DIR = './output/'


def import_image():
    img_path = [os.path.join(RES_DIR, img_name) for img_name in IMG_NAME]
    img = [np.float32(cv.imread(img_path, cv.IMREAD_GRAYSCALE)) for img_path in img_path]
    #for i in range(len(IMG_NAME)):
    #    plt.subplot(2, len(IMG_NAME) / 2 , i + 1)
    #    plt.title(IMG_NAME[i])
    #    plt.subplots_adjust(wspace=0.6, hspace=1)
    #    plt.imshow(img[i], cmap=plt.cm.gray)
    #plt.show()
    return img


def hough_line_detection(edges, dynamic_threshold=True):
    min_accept_line_num = 10
    max_accept_line_num = 50
    threshold = 50
    line_num = 0
    lines = None
    if dynamic_threshold:
        update_rate = 0.5
        iter_cnt = 0
        while line_num < min_accept_line_num or line_num > max_accept_line_num:
            print("\tIteration", iter_cnt, "Cnt:", line_num, "Threshold:", threshold)
            lines = cv.HoughLines(edges, 1, np.pi / 180, int(threshold), None, 0, 0)
            if lines is None:
                line_num = 0
            else:
                line_num = lines.shape[0]
            if threshold < 0:
                lines = cv.HoughLines(edges, 1, np.pi / 180, 0, None, 0, 0)
                break

            deviation = line_num - (max_accept_line_num + min_accept_line_num) / 2
            square_deviation = deviation * np.abs(deviation)
            threshold += update_rate * np.clip(square_deviation, -100, 100) + 10 * np.random.rand()
            iter_cnt += 1
    else:
        lines = cv.HoughLines(edges, 1, np.pi / 180, int(threshold), None, 0, 0)

    if lines is not None:
        print("Num of lines:", lines.shape[0])
    else:
        print("No line is detected")
    return lines


def hough_p_line_detection(edges):
    min_line_length = 50
    max_line_gap = 20
    lines = cv.HoughLinesP(edges, 1, np.pi / 180, 30, min_line_length, max_line_gap)
    if lines is not None:
        print("Hough P Get:", lines.shape[0])
    return lines


def print_hough_lines(img, lines):
    img_copy = img.copy()
    img_copy = np.uint8(img_copy)
    img_copy = cv.cvtColor(img_copy, cv.COLOR_GRAY2BGR)
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
            cv.line(img_copy, pt1, pt2, (0, 0, 255), 1, cv.LINE_AA)
    return img_copy


def print_hough_p_lines(img, lines):
    img_copy = img.copy()
    img_copy = np.uint8(img_copy)
    img_copy = cv.cvtColor(img_copy, cv.COLOR_GRAY2BGR)
    if lines is not None:
        for i in range(0, len(lines)):
            for x1, y1, x2, y2 in lines[i]:
                cv.line(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 1)
    return img_copy


def get_skeleton(img):
    element = cv.getStructuringElement(cv.MORPH_CROSS, (3, 3))
    img_local = img.copy()
    img_local = img_local > 15
    img_local = np.uint8(img_local) * 255
    skel = np.zeros(img_local.shape, np.uint8)
    while True:
        erode = cv.erode(img_local, element)
        temp = cv.dilate(erode, element)
        temp = cv.subtract(img_local, temp)
        skel = cv.bitwise_or(skel, temp)
        img_local = erode.copy()

        if cv.countNonZero(img_local) == 0:
            break
    return skel


def run(img, edge_detector, with_skeleton=True, with_dilated=True, with_dynamic_threshold=True):
    edge = edge_detector(img)
    max_edge = np.max(edge)
    edge = edge > max_edge * 0.2
    edge = np.uint8(edge) * 255

    if with_dilated:
        element = cv.getStructuringElement(cv.MORPH_CROSS, (3, 3))
        edge = cv.dilate(edge, element)

    if with_skeleton:
        edge = get_skeleton(edge)

    lines = hough_line_detection(edge, with_dynamic_threshold)
    lines_p = hough_p_line_detection(edge)
    img_lines = print_hough_lines(img, lines)
    img_lines_p = print_hough_p_lines(img, lines_p)
    return img_lines, edge, img_lines_p


def main():
    img = import_image()
    edge_detectors = {"Canny": canny, "Sobel": sobel, "Laplacian": laplace, "USP": usp}
    # Test case config-> (With Skeleton, With Dilated Skeleton, With Dynamic Threshold)
    test_options = [(False, False, False), (False, False, True), (True, False, True), (True, True, True)]
    for test_option in test_options:
        with_skeleton, with_dilated, with_dynamic_threshold = test_option
        filename_prefix = ''
        if with_skeleton:
            filename_prefix += 'S_'
        if with_dilated:
            filename_prefix += 'Dil_'
        if with_dynamic_threshold:
            filename_prefix += 'Dyn_'
        for img_sel in range(len(img)):
            src_img = img[img_sel]
            blur_img = cv.blur(src_img, (3, 3))
            detector_names = list(edge_detectors.keys())
            for i in range(len(detector_names)):
                detector_name = detector_names[i]
                print(detector_name)
                line_img, edge, line_p_img = run(
                    blur_img,
                    edge_detectors[detector_name],
                    with_skeleton,
                    with_dilated,
                    with_dynamic_threshold
                )

                def construct_file_name(center):
                    _filename = filename_prefix + center + "_" + str(img_sel) + "_" + detector_name + ".png"
                    _filename = os.path.join(OUTPUT_DIR, _filename)
                    print("Write to", _filename)
                    return _filename

                cv.imwrite(construct_file_name("Img"), line_img)
                cv.imwrite(construct_file_name("Img_P"), line_p_img)
                cv.imwrite(construct_file_name("Edge"), edge)


if __name__ == '__main__':
    main()
