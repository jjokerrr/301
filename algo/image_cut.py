import cv2


# opencv 读取图片是类似二维数组的读法的，左上角为原点，（row,col），和openpose不太一样，后者是（col,row）
def cut(image, left_top_pnt, right_bottom_pnt):
    """
    image:需要是ndarray
    left_top_pnt, right_bottom_pnt:需要是（row，col）格式的
    """
    x1, x2 = left_top_pnt[0], right_bottom_pnt[0]
    y1, y2 = left_top_pnt[1], right_bottom_pnt[1]

    return image[int(x1):int(x2), int(y1):int(y2)]
