import math

# 如果需要考虑并发，可以简单使用dict[id]->status来实现
MAX_NUM = 10  # 一次出场的人数
StatusArr = [0 for i in range(MAX_NUM)]  # 有限状态自动机的当前状态，0->准备/结束，1->拉，2->引，3->投，4->蹲
HeightArr = [0 for i in range(MAX_NUM)]
CountArr = [[0 for j in range(10)] for i in range(MAX_NUM)]  # 需要重新初始化，否则里面的每一个数组都是同一个
HistoryPoseData = [[] for i in range(MAX_NUM)]  # 历史数据，需要重新初始化
'''
openpose输出的数据格式：以左上角为原点，（水平长度，竖直长度，置信度）
"1": [
      1445.4921875,
      315.70257568359375,
      0.7470813989639282
    ],
'''

poses = {
    'left_elbow': (5, 6, 7),
    'left_hand': (1, 5, 7),
    'left_knee': (12, 13, 14),
    'left_ankle': (5, 12, 14),
    'right_elbow': (2, 3, 4),
    'right_hand': (1, 2, 4),
    'right_knee': (9, 10, 11),
    'right_ankle': (2, 9, 11)
}

PREPARING = 0
PULL = 1
STRETCH = 2
THROW = 3
SQUAT = 4
LEAVE = 5


def reset():
    global StatusArr, HeightArr, CountArr, MAX_NUM
    for i in range(MAX_NUM):
        StatusArr[i] = 0
        HeightArr[i] = 0
        CountArr[i] = [0 for i in range(10)]
        HistoryPoseData[i] = []


def get_dist_between_2_points(key_points_i, p1, p2):
    return math.sqrt(
        (key_points_i[p1][0] - key_points_i[p2][0]) ** 2 + (key_points_i[p1][1] - key_points_i[p2][1]) ** 2)


# def angle_between_points(p0, p1, p2):
#     a = (p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2
#     b = (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2
#     c = (p2[0] - p0[0]) ** 2 + (p2[1] - p0[1]) ** 2
#     if a * b == 0:
#         return -1.0
#
#     return math.acos((a + b - c) / math.sqrt(4 * a * b)) * 180 / math.pi


# def get_angle_point(human, pos):
#     # 返回构成各部位的三个点坐标
#     pnts = []
#
#     if pos in poses:
#         pos_list = poses[pos]
#     else:
#         print('Unknown  [%s]', pos)
#         return pnts
#
#     for i in range(3):
#         if human[pos_list[i]][2] <= 0.1:
#             # print('component [%d] incomplete' % (pos_list[i]))
#             return pnts
#         pnts.append((int(human[pos_list[i]][0]), int(human[pos_list[i]][1])))
#     return pnts


# def cal_angle(human, pos):
#     # 计算人体某个关节的角度
#     pnts = get_angle_point(human, pos)
#     if len(pnts) != 3:
#         # print('component incomplete')
#         return -1
#     angle = 0
#     if pnts is not None:
#         angle = angle_between_points(pnts[0], pnts[1], pnts[2])
#     return angle


def get_point(key_point_i, point_id):
    if key_point_i[point_id][0] == 0:
        raise NameError
    return key_point_i[point_id][0], key_point_i[point_id][1]


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


# 求身高和宽度的比例，排除手部的计算
def get_height_width_ratio(pose_data_for_one):
    included_pnt = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    min_x = 10000000
    min_y = 10000000
    max_x = 0
    max_y = 0

    for i in range(len(pose_data_for_one)):
        if i not in included_pnt:
            continue

        try:
            get_point(pose_data_for_one, i)
        except Exception:
            continue
        min_x = min(min_x, pose_data_for_one[i][0])
        min_y = min(min_y, pose_data_for_one[i][1])
        max_x = max(max_x, pose_data_for_one[i][0])
        max_y = max(max_y, pose_data_for_one[i][1])
    return (max_y - min_y) / (max_x - min_x)


# 求出openpose输出结果中最大y轴点和最小y轴点之间的差距
def get_y_gap_height(pose_data_for_one):
    min_y = 10000000
    max_y = 0
    for i in range(len(pose_data_for_one)):
        try:
            get_point(pose_data_for_one, i)
        except Exception:
            continue
        min_y = min(min_y, pose_data_for_one[i][1])
        max_y = max(max_y, pose_data_for_one[i][1])
    return max_y - min_y


def get_status_count(person_id, status):
    global CountArr
    return CountArr[person_id][status]


# 判断人物是否是站在原地的,todo 数据为0
def check_if_person_is_standing(id):
    if len(HistoryPoseData[id]) < 11:
        return False
    return abs(HistoryPoseData[id][-1][0][0] - HistoryPoseData[id][-11][0][0]) < 100


def identify_single_person(id, pose_data_for_one, algo_type):
    global CountArr, StatusArr, HistoryPoseData
    # print("person_id=%d action_before_switch=%d algo_log={" % (id, StatusArr[id]))
    # 投远 --
    if algo_type == 4:
        status = __identify_single_person_throwFar(id, pose_data_for_one)
        # print(status)
    # 投准 --
    elif algo_type == 5:
        status = __identify_single_person_throwDirect(id, pose_data_for_one)
        print(status)
    # 侧甩 --
    elif algo_type == 0:
        status = __identify_single_person_sideThrow(id, pose_data_for_one)
    # 滚手榴弹 --
    elif algo_type == 1:
        status = __identify_single_person_roll(id, pose_data_for_one)
    # 抛手榴弹 --
    elif algo_type == 2:
        status = __identify_single_person_throw(id, pose_data_for_one)
    # 塞手榴弹
    elif algo_type == 3:
        status = __identify_single_person_stuff(id, pose_data_for_one)
    # 默认为投远
    else:
        status = __identify_single_person_throwFar(id, pose_data_for_one)
    # print("}")
    CountArr[id][status] += 1
    HistoryPoseData[id].append(pose_data_for_one)
    return status


# -------------- 投远 -----------------------------
def __identify_single_person_throwFar(id, pose_data_for_one):
    global StatusArr, HeightArr
    # try:
    #     angle_between_thighs = get_angle_between_lines(pose_data_for_one, 9, 10, 12, 13)
    #     # print("[angle:%f]" % angle_between_thighs)
    #     width_of_shoulder = get_dist_between_2_points(pose_data_for_one, 2, 5)  # 两肩之间的距离
    #     dist_between_hands = get_dist_between_2_points(pose_data_for_one, 4, 7)  # 手腕关节点之间的距离
    #     height = max(get_point(pose_data_for_one, 22)[1], get_point(pose_data_for_one, 19)[1]) - \
    #              min(get_point(pose_data_for_one, 15)[1], get_point(pose_data_for_one, 16)[1])  # 人像高度的粗略估计
    #     right_hand_point_vertical_value = get_point(pose_data_for_one, 4)[1]
    #     shoulder_center_point_vertical_value = get_point(pose_data_for_one, 1)[1]
    #     height_of_stomach = (get_point(pose_data_for_one, 1)[1] + get_point(pose_data_for_one, 8)[1]) / 2
    #     height_of_left_hand_point = get_point(pose_data_for_one, 7)[1]
    # except Exception:
    #     # return StatusArr[id]
    #     pass
    if StatusArr[id] == 0:  # 准备阶段
        if check_if_person_is_standing(id):  # 站立不动时才能进入下一个阶段
            StatusArr[id] = 1
        pass  # 新版本把1视为开始状态

        try:
            angle_between_thighs = get_angle_between_lines(pose_data_for_one, 23, 27, 24, 28)
            height_of_stomach = (get_point(pose_data_for_one, 1)[1] + get_point(pose_data_for_one, 8)[1]) / 2
            height_of_left_hand_point = get_point(pose_data_for_one, 7)[1]
            angle_of_left_leg = get_angle_between_lines(pose_data_for_one, 25, 23, 25, 27)
            angle_of_right_leg = get_angle_between_lines(pose_data_for_one, 26, 24, 26, 28)
        except Exception:
            return StatusArr[id]

        # 大腿之间的角度小于20度且左手末端高度高于肚子，并且两腿是直的
        print("angle_between_thighs=%f" % angle_between_thighs)
        print("height_of_stomach=%f" % height_of_stomach)
        print("height_of_left_hand_point=%f" % height_of_left_hand_point)
        print("angle_of_left_leg=%f" % angle_of_left_leg)
        print("angle_of_right_leg=%f" % angle_of_right_leg)
        if angle_between_thighs < 20 and height_of_left_hand_point < height_of_stomach \
                and angle_of_left_leg > 160 and angle_of_right_leg > 160:
            StatusArr[id] = 1
    elif StatusArr[id] == 1:  # 拉
        HeightArr[id] = max(HeightArr[id], get_y_gap_height(pose_data_for_one))  # 更新一下身高信息表，为后续的判断蹲做准备
        print("height:%f" % HeightArr[id])
        try:
            angle_between_thighs = get_angle_between_lines(pose_data_for_one, 23, 27, 24, 28)
        except Exception:
            return StatusArr[id]
        print("angle_between_thighs=%f" % angle_between_thighs)
        if angle_between_thighs > 30:  # 大腿之间的角度超过30度
            StatusArr[id] = 2
    elif StatusArr[id] == 2:  # 引
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 20)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_vertical_value < shoulder_center_point_vertical_value:  # 右手高度超过肩部中心
            StatusArr[id] = 3
    elif StatusArr[id] == 3:  # 投
        # try:
        #     width_of_shoulder = get_dist_between_2_points(pose_data_for_one, 2, 5)  # 两肩之间的距离
        #     height = max(get_point(pose_data_for_one, 22)[1], get_point(pose_data_for_one, 19)[1]) - \
        #              min(get_point(pose_data_for_one, 15)[1], get_point(pose_data_for_one, 16)[1])  # 人像高度的粗略估计
        # except Exception:
        #     return StatusArr[id]
        # height_width_ratio = height / width_of_shoulder
        # if height / width_of_shoulder < 2:
        #     StatusArr[id] = 4

        # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        # if height_width_ratio < 2:
        #     StatusArr[id] = 4
        current_height_ratio = get_y_gap_height(pose_data_for_one) / HeightArr[id]
        if current_height_ratio < 0.75:
            StatusArr[id] = 4
        print("current_height_ratio=%f" % current_height_ratio)
        print("MaxHeightFromBeginning=%f" % HeightArr[id])

    elif StatusArr[id] == 4:  # 蹲
        # try:
        #     width_of_shoulder = get_dist_between_2_points(pose_data_for_one, 2, 5)  # 两肩之间的距离
        #     height = max(get_point(pose_data_for_one, 22)[1], get_point(pose_data_for_one, 19)[1]) - \
        #              min(get_point(pose_data_for_one, 15)[1], get_point(pose_data_for_one, 16)[1])  # 人像高度的粗略估计
        # except Exception:
        #     return StatusArr[id]
        # height_width_ratio = height / width_of_shoulder
        # if height / width_of_shoulder > 2:
        #     StatusArr[id] = 0
        # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        # print("ratio: %f" % height_width_ratio)
        # if height_width_ratio > 2:
        #     StatusArr[id] = 5
        current_height_ratio = get_y_gap_height(pose_data_for_one) / HeightArr[id]
        if current_height_ratio > 0.75:
            StatusArr[id] = 5
        print("current_height_ratio=%f" % current_height_ratio)
    elif StatusArr[id] == 5:  # 结束离场
        return StatusArr[id]

    return StatusArr[id]


# -------------- 投准 -----------------------------
def __identify_single_person_throwDirect(id, pose_data_for_one):
    global StatusArr, HeightArr
    if StatusArr[id] == 0:  # 准备阶段
        try:
            angle_between_thighs = get_angle_between_lines(pose_data_for_one, 23, 27, 24, 28)
            angle_between_legs = 180 - get_angle_between_lines(pose_data_for_one, 23, 25, 25, 27)
        except Exception:
            return StatusArr[id]

        # 半蹲进入下一阶段
        # 大腿之间的角度大于60度且左大小腿之间角度位于70-100度之间
        print("angle_between_thighs=%f" % angle_between_thighs)
        print("angle_between_legs=%f" % angle_between_legs)
        if angle_between_thighs > 60 and angle_between_legs < 100 and angle_between_legs > 70:
            StatusArr[id] = 1
    elif StatusArr[id] == 1:  # 拉
        HeightArr[id] = max(HeightArr[id], get_y_gap_height(pose_data_for_one))  # 更新一下身高信息表，为后续的判断蹲做准备
        print("height:%f" % HeightArr[id])
        try:
            angle_between_thighs = get_angle_between_lines(pose_data_for_one, 23, 27, 24, 28)
        except Exception:
            return StatusArr[id]
        print("angle_between_thighs=%f" % angle_between_thighs)
        if angle_between_thighs > 90:  # 大腿之间的角度超过90度
            StatusArr[id] = 2
    elif StatusArr[id] == 2:  # 引
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 20)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_vertical_value < shoulder_center_point_vertical_value:  # 右手高度超过肩部中心
            StatusArr[id] = 3
    elif StatusArr[id] == 3:  # 投
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 20)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_vertical_value > shoulder_center_point_vertical_value:  # 右手高度低于肩部中心
            StatusArr[id] = 5

    # 投完结束离场    
    elif StatusArr[id] == 5:  # 结束离场
        return StatusArr[id]

    return StatusArr[id]

# -------------- 侧甩 -----------------------------
def __identify_single_person_sideThrow(id, pose_data_for_one):
    global StatusArr, HeightArr
    if StatusArr[id] == 0:  # 准备阶段
        try:
            angle_between_thighs = get_angle_between_lines(pose_data_for_one, 23, 27, 24, 28)
            angle_between_left_arms = 180 - get_angle_between_lines(pose_data_for_one, 11, 13, 13, 15)
            
        except Exception:
            return StatusArr[id]

        # 卧倒进入下一阶段
        # 大腿之间的角度大于60度
        print("angle_between_thighs=%f" % angle_between_thighs)
        print("angle_between_left_arms=%f" % angle_between_left_arms)
        if angle_between_thighs > 60:
            StatusArr[id] = 1
    elif StatusArr[id] == 1:  # 拉
        # 右臂与左大臂夹角大于30度进入引阶段
        try:
            angle_between_right_arm_and_left = get_angle_between_lines(pose_data_for_one, 11, 13, 12, 16)
        except Exception:
            return StatusArr[id]
        print("angle_between_right_arm_and_left=%f" % angle_between_right_arm_and_left)
        if angle_between_right_arm_and_left > 30:  # 右臂与左大臂夹角大于30度
            StatusArr[id] = 2
    elif StatusArr[id] == 2:  # 引
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 20)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_vertical_value < shoulder_center_point_vertical_value:  # 右手高度超过肩部中心
            StatusArr[id] = 3
    elif StatusArr[id] == 3:  # 投
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 20)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_vertical_value > shoulder_center_point_vertical_value:  # 右手高度低于肩部中心
            StatusArr[id] = 5

    # 投完结束离场    
    elif StatusArr[id] == 5:  # 结束离场
        return StatusArr[id]

    return StatusArr[id]

# -------------- 滚手榴弹 -----------------------------
def __identify_single_person_roll(id, pose_data_for_one):
    global StatusArr, HeightArr
    if StatusArr[id] == 0:  # 准备阶段
        try:
            angle_between_thighs = get_angle_between_lines(pose_data_for_one, 23, 25, 24, 26)
            angle_between_left_arms = 180 - get_angle_between_lines(pose_data_for_one, 11, 13, 13, 15)
            
        except Exception:
            return StatusArr[id]

        # 下蹲进入下一阶段
        # 大腿之间的角度大于90度且左大小臂之间角度小于120度
        print("angle_between_thighs=%f" % angle_between_thighs)
        print("angle_between_left_arms=%f" % angle_between_left_arms)
        if angle_between_thighs > 90 and angle_between_left_arms < 120:
            StatusArr[id] = 1
    elif StatusArr[id] == 1:  # 拉
        # 右臂与左大臂夹角大于30度进入引阶段
        try:
            angle_between_right_arm_and_left = get_angle_between_lines(pose_data_for_one, 11, 13, 12, 16)
        except Exception:
            return StatusArr[id]
        print("angle_between_right_arm_and_left=%f" % angle_between_right_arm_and_left)
        if angle_between_right_arm_and_left > 30:  # 右臂与左大臂夹角大于30度
            StatusArr[id] = 2
    elif StatusArr[id] == 2:  # 引
        try:
            angle_between_right_arms = 180 - get_angle_between_lines(pose_data_for_one, 12, 14, 14, 16)
            right_hand_point_horizontal_value = get_point(pose_data_for_one, 20)[0]
            shoulder_center_point_horizontal_value = get_point(pose_data_for_one, 12)[0]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_horizontal_value=%f" % right_hand_point_horizontal_value)
        print("shoulder_center_point_horizontal_value=%f" % shoulder_center_point_horizontal_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_horizontal_value < shoulder_center_point_horizontal_value and angle_between_right_arms > 80:  # 右手在右肩往左并且大小臂夹角超过80度
            StatusArr[id] = 3
    elif StatusArr[id] == 3:  # 投
        try:
            angle_between_right_arms = 180 - get_angle_between_lines(pose_data_for_one, 12, 14, 14, 16)
            right_hand_point_horizontal_value = get_point(pose_data_for_one, 20)[0]
            shoulder_center_point_horizontal_value = get_point(pose_data_for_one, 12)[0]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_horizontal_value=%f" % right_hand_point_horizontal_value)
        print("shoulder_center_point_horizontal_value=%f" % shoulder_center_point_horizontal_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_horizontal_value > shoulder_center_point_horizontal_value and angle_between_right_arms < 80:  # 右手在右肩往右且右大小臂夹角小于80度
            StatusArr[id] = 5

    # 投完结束离场    
    elif StatusArr[id] == 5:  # 结束离场
        return StatusArr[id]

    return StatusArr[id]

# -------------- 抛手榴弹 -----------------------------
def __identify_single_person_throw(id, pose_data_for_one):
    global StatusArr, HeightArr
    if StatusArr[id] == 0:  # 准备阶段
        if check_if_person_is_standing(id):  # 站立不动时才能进入下一个阶段
            StatusArr[id] = 1
        pass  # 新版本把1视为开始状态

        try:
            dis_between_fists = get_dist_between_2_points(pose_data_for_one, 20, 19)
            len_of_left_arm = get_dist_between_2_points(pose_data_for_one, 13, 15)
            angle_of_left_arm = get_angle_between_lines(pose_data_for_one, 13, 11, 13, 15)
            angle_of_right_arm = get_angle_between_lines(pose_data_for_one, 14, 12, 14, 16)
            
        except Exception:
            return StatusArr[id]

        # 两拳距离小于小臂长度且两臂角度在90左右
        print("dis_between_fists=%f" % dis_between_fists)
        print("len_of_left_arm=%f" % len_of_left_arm)
        print("angle_of_left_arm=%f" % angle_of_left_arm)
        print("angle_of_right_arm=%f" % angle_of_right_arm)
        if dis_between_fists < len_of_left_arm and 70 <= angle_of_left_arm <= 110 and  70 <= angle_of_right_arm <= 110:
            StatusArr[id] = 1
    elif StatusArr[id] == 1:  # 拉
        HeightArr[id] = max(HeightArr[id], get_y_gap_height(pose_data_for_one))  # 更新一下身高信息表，为后续的判断蹲做准备
        print("height:%f" % HeightArr[id])
        try:
            angle_of_right_arm = get_angle_between_lines(pose_data_for_one, 14, 12, 14, 16)
        except Exception:
            return StatusArr[id]
        print("angle_of_right_arm=%f" % angle_of_right_arm)
        if angle_of_right_arm > 140: # 右手角度大于140
            StatusArr[id] = 2
    elif StatusArr[id] == 2:  # 引
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 18)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)

        if right_hand_point_vertical_value > shoulder_center_point_vertical_value:  # 右手高度超过肩部中心
            StatusArr[id] = 3
    elif StatusArr[id] == 3:  # 投
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 18)[1]
            head_center_point_vertical_value = get_point(pose_data_for_one, 0)[1]
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("head_center_point_vertical_value=%f" % head_center_point_vertical_value)
        if right_hand_point_vertical_value < head_center_point_vertical_value:  # 右手高度没超过头部中心
            StatusArr[id] = 4
    #     current_height_ratio = get_y_gap_height(pose_data_for_one) / HeightArr[id]
    #     if current_height_ratio < 0.75:
    #         StatusArr[id] = 4
    #     print("current_height_ratio=%f" % current_height_ratio)
    #     print("MaxHeightFromBeginning=%f" % HeightArr[id])

    # elif StatusArr[id] == 4:  # 蹲
    #     current_height_ratio = get_y_gap_height(pose_data_for_one) / HeightArr[id]
    #     if current_height_ratio > 0.75:
    #         StatusArr[id] = 5
    #     print("current_height_ratio=%f" % current_height_ratio)
    # elif StatusArr[id] == 5:  # 结束离场
    #     return StatusArr[id]

    return StatusArr[id]

# -------------- 塞手榴弹 -----------------------------
def __identify_single_person_stuff(id, pose_data_for_one):
    global StatusArr, HeightArr
    if StatusArr[id] == 0:  # 准备阶段
        if check_if_person_is_standing(id):  # 站立不动时才能进入下一个阶段
            StatusArr[id] = 1
        pass  # 新版本把1视为开始状态

        try:
            dis_between_fists = get_dist_between_2_points(pose_data_for_one, 20, 19)
            len_of_left_arm = get_dist_between_2_points(pose_data_for_one, 13, 15)
            angle_of_left_arm = get_angle_between_lines(pose_data_for_one, 13, 11, 13, 15)
            angle_of_right_arm = get_angle_between_lines(pose_data_for_one, 14, 12, 14, 16)
        except Exception:
            return StatusArr[id]

         # 两拳距离小于小臂长度且两臂角度在90左右
        print("dis_between_fists=%f" % dis_between_fists)
        print("len_of_left_arm=%f" % len_of_left_arm)
        print("angle_of_left_arm=%f" % angle_of_left_arm)
        print("angle_of_right_arm=%f" % angle_of_right_arm)
        if dis_between_fists < len_of_left_arm and 70 <= angle_of_left_arm <= 110 and  70 <= angle_of_right_arm <= 110:
            StatusArr[id] = 1
    elif StatusArr[id] == 1:  # 拉
        HeightArr[id] = max(HeightArr[id], get_y_gap_height(pose_data_for_one))  # 更新一下身高信息表，为后续的判断蹲做准备
        print("height:%f" % HeightArr[id])
        try:
             # 左臂夹角
            angle_between_left_arm = get_angle_between_lines(pose_data_for_one, 11, 13, 13, 15)
            # 右臂夹角
            angle_between_right_arm = get_angle_between_lines(pose_data_for_one, 12, 14, 14, 22)
        except Exception:
            return StatusArr[id]
        print(f'angle_between_left_arm = {angle_between_left_arm}, angle_between_right_arm = {angle_between_right_arm}')
        # 双手弯曲
        if angle_between_left_arm < 180 or angle_between_right_arm < 180 :  
            StatusArr[id] = 3
    elif StatusArr[id] == 2:  # 引
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 20)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)
        # print("height_width_ratio=%f" % height_width_ratio)

        if right_hand_point_vertical_value < shoulder_center_point_vertical_value:  # 右手高度超过肩部中心
            StatusArr[id] = 3
    elif StatusArr[id] == 3:  # 投
        try:
            right_hand_point_vertical_value = get_point(pose_data_for_one, 20)[1]
            shoulder_center_point_vertical_value = get_point(pose_data_for_one, 12)[1]
            # 右臂夹角
            angle_between_right_arm = get_angle_between_lines(pose_data_for_one, 12, 14, 14, 22)
            # height_width_ratio = get_height_width_ratio(pose_data_for_one)
        except Exception:
            return StatusArr[id]
        print("right_hand_point_vertical_value=%f" % right_hand_point_vertical_value)
        print("shoulder_center_point_vertical_value=%f" % shoulder_center_point_vertical_value)
        print("angle_between_right_arm=%f" % angle_between_right_arm)

        if right_hand_point_vertical_value <= shoulder_center_point_vertical_value and angle_between_right_arm >= 150:  # 右手高度超过肩部中心且将近直臂
            StatusArr[id] = 5

    elif StatusArr[id] == 4:  # 蹲
        current_height_ratio = get_y_gap_height(pose_data_for_one) / HeightArr[id]
        if current_height_ratio > 0.75:
            StatusArr[id] = 5
        print("current_height_ratio=%f" % current_height_ratio)
    elif StatusArr[id] == 5:  # 结束离场
        return StatusArr[id]

    return StatusArr[id]