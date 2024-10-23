import sys

"""
根据关键点获取对应人物的bbox

:poseKeypoints_i: 第i个人的关键点信息
:returns: 返回一个列表, 第i个人的bbox信息, 即左上和右下两点坐标(x1,y1)(x2,y2)
"""
person_num = 10
BoxArray = [[[100000000, 100000000], [0, 0]] for i in range(person_num)]


def reset():
    global BoxArray, person_num
    for i in range(person_num):
        BoxArray = [[[100000000, 100000000], [0, 0]] for i in range(person_num)]


# 第二版
def getBBox2(poseKeypoints_i, id, action_id):
    global BoxArray, person_num
    box_res = getBBox(poseKeypoints_i)
    if 1 <= action_id <= 4:
        BoxArray[id][0][0] = min(BoxArray[id][0][0], box_res[0][0])
        BoxArray[id][0][1] = min(BoxArray[id][0][1], box_res[0][1])
        BoxArray[id][1][0] = max(BoxArray[id][1][0], box_res[1][0])
        BoxArray[id][1][1] = max(BoxArray[id][1][1], box_res[1][1])
    return BoxArray[id]


def getBBox(poseKeypoints_i):
    # excluded_pnt = [3, 4, 6, 7]
    bbox = []
    max_x = 0
    min_x = sys.maxsize
    max_y = 0
    min_y = sys.maxsize

    for j in range(0, len(poseKeypoints_i)):
        if poseKeypoints_i[j][0] <= 0 and poseKeypoints_i[j][1] <= 0:
            continue

        if poseKeypoints_i[j][0] < min_x:
            min_x = poseKeypoints_i[j][0]

        if poseKeypoints_i[j][0] > max_x:
            max_x = poseKeypoints_i[j][0]

        if poseKeypoints_i[j][1] < min_y:
            min_y = poseKeypoints_i[j][1]

        if poseKeypoints_i[j][1] > max_y:
            max_y = poseKeypoints_i[j][1]

    x_gap = max_x - min_x
    y_gap = max_y - min_y
    x_expand_side_ratio = 0.4
    y_expand_side_ratio = 0.2
    bbox.append([min_x - x_gap * x_expand_side_ratio, min_y - y_gap * y_expand_side_ratio])
    bbox.append([max_x + x_gap * x_expand_side_ratio, max_y + y_gap * y_expand_side_ratio])

    return bbox


"""
返回第person_ID个人的第point_ID个关键点

:person_ID: person ID
:point_ID: point ID
:key_points: 关键点
:returns key_points: 返回关键点(x, y)
"""


def getPoint(person_ID, point_ID, key_points):
    return (key_points[person_ID][point_ID][0], key_points[person_ID][point_ID][1])


"""
根据openpose处理结果将人物下标与图中位置进行对应,从0开始

:output_datum: openpose处理结果
:returns key_points: 返回一个列表，每个对象为一个人的关键点信息
:returns bboxes: 返回一个列表, 每个对象为一个人的bbox信息, 即左上和右下两点坐标(x1,y1)(x2,y2)
"""


def sort_func(item):
    cnt = 0
    avg = 0
    for tup in item[0]:
        if tup[0] != 0.0:
            avg += tup[0]
            cnt += 1
    return avg / cnt


def parse(poseKeypoints):
    # 人数
    human_count = len(poseKeypoints)

    key_points = []
    bboxes = []
    temp = []

    for i in range(0, human_count):
        bbox = getBBox(poseKeypoints[i])
        temp.append((poseKeypoints[i], bbox))

    temp.sort(key=sort_func)  # 所有点的x坐标平均
    for i in range(human_count):
        key_points.append(temp[i][0])
        bboxes.append(temp[i][1])

    return key_points, bboxes
