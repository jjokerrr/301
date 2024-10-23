import json
import math

import numpy

"""
计算直线ab, cd构成的夹角

:key_points_i: 第i个人的关键点
:a, b, c, d: 关键点下标
:returns: 返回角度
"""


def get_angle_between_lines(key_points_i, a, b, c, d):
    if key_points_i[a][0] == 0 or key_points_i[b][0] == 0 or key_points_i[c][0] == 0 or key_points_i[d][0] == 0:
        raise NameError
    vector_ab = (key_points_i[b][0] - key_points_i[a][0], key_points_i[b][1] - key_points_i[a][1])
    vector_cd = (key_points_i[d][0] - key_points_i[c][0], key_points_i[d][1] - key_points_i[c][1])

    # ab·cd
    dot_product = vector_ab[0] * vector_cd[0] + vector_ab[1] * vector_cd[1]

    # |ab|, |cd|
    magnitude_ab = math.sqrt(vector_ab[0] ** 2 + vector_ab[1] ** 2)
    magnitude_cd = math.sqrt(vector_cd[0] ** 2 + vector_cd[1] ** 2)

    cos_angle = dot_product / (magnitude_ab * magnitude_cd)

    # 修正可能出现的浮点数精度问题
    cos_angle = max(min(cos_angle, 1), -1)

    # 计算夹角（以度为单位）
    angle = math.degrees(math.acos(cos_angle))
    return angle


"""
计算直线ab 与水平or垂直方向构成的夹角

:key_points_i: 第i个人的关键点
:a, b: 关键点下标
:direction: 0水平，1垂直
:returns: 返回角度
"""


def get_angle_by_direction(key_points_i, a, b, direction):
    if key_points_i[a][0] == 0 or key_points_i[b][0] == 0:
        raise NameError

    vector_ab = (key_points_i[b][0] - key_points_i[a][0], key_points_i[b][1] - key_points_i[a][1])
    if direction == 0:
        vector_cd = (-180, 0)
    else:
        vector_cd = (0, 180)

    # ab·cd
    dot_product = vector_ab[0] * vector_cd[0] + vector_ab[1] * vector_cd[1]

    # |ab|, |cd|
    magnitude_ab = math.sqrt(vector_ab[0] ** 2 + vector_ab[1] ** 2)
    magnitude_cd = math.sqrt(vector_cd[0] ** 2 + vector_cd[1] ** 2)

    cos_angle = dot_product / (magnitude_ab * magnitude_cd)

    # 修正可能出现的浮点数精度问题
    cos_angle = max(min(cos_angle, 1), -1)

    # 计算夹角（以度为单位）
    angle = math.degrees(math.acos(cos_angle))

    return angle


"""
根据poses计算预设姿势的角度
或
计算直线ab, cd构成的夹角

:key_points: 关键点
:a, b, c, d: 关键点下标
:returns: 返回角度的字典poses:angle
"""


#
# def getAngle(key_points, a=None, b=None, c=None, d=None):
#     anses = {}
#     human_count = len(key_points)
#
#     # 计算第i个人对应角度
#     for i in range(human_count):
#         ans = {}
#
#         # 指定两线段
#         if a is not None and b is not None and c is not None and d is not None:
#             key = ((a, b), (c, d))
#             ans = getAngleBetweenLines(key_points[i], a, b, c, d)
#
#         # 未指定线段，按poses计算
#         else:
#             for pos in poses:
#                 a, b, c, d = poses[pos]
#                 ans[pos] = getAngleBetweenLines(key_points[i], a, b, c, d)
#
#         anses[i] = ans
#
#     return anses

def swap_x_and_y(pnt):
    return int(pnt[1]), int(pnt[0])


def read_json_from_path(path):
    content = ''
    with open(path) as f:
        content = f.read()
    data = json.loads(content)
    return data

# if __name__ == '__main__':
#     pnt = numpy.float64(1.)
#     print(int(pnt))
