import phase_identify
import utils
import math
import random
from algo.utils import read_json_from_path

plan = read_json_from_path('algo/mock_data/plan.json')

MIN_DIS_ARR = [float('inf') for i in range(10)]
EVAL_DATA_ARR = [None for j in range(10)]


def get_dist_between_2_points(key_points_i, p1, standard_data, p2):
    return math.sqrt(
        (key_points_i[p1][0] - standard_data[str(p2)][0]) ** 2 + (
                key_points_i[p1][1] - standard_data[str(p2)][1]) ** 2)


def get_min_distance_data(person_id, pose_data_for_one, pre_action_id, action_id, algo_type):
    """
    返回action_id阶段中，与标准动作差异最小的数据
    """
    if action_id <= 0 or ((algo_type != 3 and action_id > 3) or (algo_type == 3 and action_id > 2)):
        return None

    global MIN_DIS_ARR
    global EVAL_DATA_ARR
    # 恢复为初始值
    if pre_action_id != action_id:
        MIN_DIS_ARR[person_id] = float('inf')
        EVAL_DATA_ARR[person_id] = None

    # 将algo_type映射到文件夹名称
    # 场景类型：
    # 1. 投远 => algo_type = 4
    # 2. 投准 => algo_type = 5
    # 3. 侧甩 => algo_type = 0
    # 4. 滚手榴弹 => algo_type = 1
    # 5. 抛手榴弹 => algo_type = 2
    # 6. 塞手榴弹 => algo_type = 3
    algo_map = {
        0: "sideThrow",
        1: "roll",
        2: "throw",
        3: "stuff",
        4: "throwFar",
        5: "throwDirect"
    }
    # 本地视频用这个
    standard_data = read_json_from_path(f'algo/mock_data/{algo_map[algo_type]}/standard_data_' + str(action_id) + '_fixed.json')

    # 摄像头用这个
    standard_data = read_json_from_path(f'algo/mock_data/{algo_map[algo_type]}/standard_data_' + str(action_id) + '_2560*1440_fixed.json')

    distance = 0
    for i in range(len(standard_data)):
        distance += get_dist_between_2_points(pose_data_for_one, i, standard_data, i)

    if distance < MIN_DIS_ARR[person_id]:
        MIN_DIS_ARR[person_id] = distance
        EVAL_DATA_ARR[person_id] = pose_data_for_one

    return EVAL_DATA_ARR[person_id]


def get_distance_by_error_data(pose_data_for_one):
    """
    返回与错误动作差异的距离
    """
    error_data_of_shoulder = read_json_from_path('algo/mock_data/error_data_of_shoulder.json')
    # 测试帧和错误帧，脖子坐标的距离
    base_distance = get_dist_between_2_points(pose_data_for_one, 1, error_data_of_shoulder, 1)

    distance = 0
    for i in range(len(error_data_of_shoulder)):
        distance += get_dist_between_2_points(pose_data_for_one, i, error_data_of_shoulder, i)
    # 通过减去人物所处位置的差异，获得动作差异的距离
    distance -= 25 * base_distance
    return distance

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

def get_result(action_id, eval_way, state, index_for_reason):
    """
    action_id: 准备-0，拉-1，引-2，投-3，蹲-4
    eval_way: 评估的内容
    state: 红-0， 黄-1，绿-2
    index_for_reason: 原因的下标
    return <state, result, [suggestion_list], [video_url_list], reason>
    """
    plan_result_list = plan[str(action_id)][eval_way][str(state)]["result"]
    plan_suggestion_list = plan[str(action_id)][eval_way][str(state)]["suggestion"]
    plan_video_url_list = plan[str(action_id)][eval_way][str(state)]["video_url"]
    plan_reason = plan[str(action_id)][eval_way][str(state)]["reason"][index_for_reason]
    # 下标的随机值
    random_index_for_result = random.randint(0, len(plan_result_list) - 1)
    random_index_for_suggestion = random.randint(0, len(plan_suggestion_list) - 1)

    # 针对投阶段的"肩部位置前移"评估，特例情况为：需要有多条suggestion和url
    if action_id == 3:
        return state, plan_result_list[random_index_for_result], \
            plan_suggestion_list, plan_video_url_list, plan_reason
    else:
        return state, plan_result_list[random_index_for_result], \
            [plan_suggestion_list[random_index_for_suggestion], ], [plan_video_url_list[
                                                                        random_index_for_suggestion], ], plan_reason


def eval_pull(pose_data_for_one):
    result_list = []
    try:
        # 评估1：拉保险销方向，左手应有大幅度运动
        # 左小臂与垂直方向的夹角
        angle_of_pull = utils.get_angle_by_direction(pose_data_for_one, 6, 7, 1)
        if angle_of_pull > 20:
            result_list.append(get_result(1, "direction", 2, 0))
        else:
            result_list.append(get_result(1, "direction", 1, 0))
    except NameError:
        # 需要评估的点缺失，直接返回动作标准
        result_list.append(get_result(1, "direction", 2, 0))

    return result_list


def eval_stretch(pose_data_for_one):
    result_list = []
    try:
        # 评估1：比较右手与右肩的垂直方向坐标，应略低于右肩
        right_hand_point_vertical_value = phase_identify.get_point(pose_data_for_one, 4)[1]
        right_shoulder_point_vertical_value = phase_identify.get_point(pose_data_for_one, 2)[1]
        difference = right_shoulder_point_vertical_value - right_hand_point_vertical_value
        # 人像高度新版计算方式
        height = phase_identify.get_y_gap_height(pose_data_for_one)
        # 评估1法1：弹体略低于右肩
        if 0.05 < (difference / height) < 0.15:
            result_list.append(get_result(2, "height", 2, 0))
        else:
            result_list.append(get_result(2, "height", 1, 0))
        # 评估1法2：右手和右肩连线 与 x轴 的夹角角度（法1效果不好再实现）
    except NameError:
        result_list.append(get_result(2, "height", 2, 0))

    try:
        # 评估2：右脚应后撤
        width_of_foot = phase_identify.get_dist_between_2_points(pose_data_for_one, 21, 24)  # 两脚跟之间的距离
        width_of_shoulder = phase_identify.get_dist_between_2_points(pose_data_for_one, 2, 5)  # 两肩之间的距离
        if width_of_foot < 1.3 * width_of_shoulder:
            result_list.append(get_result(2, "foot", 1, 0))
        else:
            result_list.append(get_result(2, "foot", 2, 0))
    except NameError:
        result_list.append(get_result(2, "foot", 2, 0))

    try:
        # 评估3：右腿膝关节弓步角度应大于100度
        angle_between_right_leg = 180 - utils.get_angle_between_lines(pose_data_for_one, 9, 10, 10, 11)
        if angle_between_right_leg <= 100:
            result_list.append(get_result(2, "angle", 1, 0))
        else:
            result_list.append(get_result(2, "angle", 2, 0))
    except NameError:
        result_list.append(get_result(2, "angle", 2, 0))

    return result_list

# ------------------------ 投远 -------------------------
def eval_throwFar(person_id, pose_data_for_one):
    result_list = []

    try:
        # 评估1：肘部低于肩部
        # 比较右肘与右肩的垂直方向坐标，右肘不应低于右肩
        right_elbow_point_vertical_value = phase_identify.get_point(pose_data_for_one, 14)[1]
        right_shoulder_point_vertical_value = phase_identify.get_point(pose_data_for_one, 12)[1]
        print("right_elbow: ", right_elbow_point_vertical_value)
        print("right_shoulder: ", right_shoulder_point_vertical_value)
        if right_elbow_point_vertical_value <= right_shoulder_point_vertical_value:
            result_list.append(get_result(3, "height", 2, 0))
        else:
            result_list.append(get_result(3, "height", 0, 0))
    except NameError:
        result_list.append(get_result(3, "height", 2, 0))

    # 评估2：挥臂不快
    # 出手速度随机出，范围是16-21m/s，>=15m/s是标准
    speed = random.uniform(16, 21)
    if speed < 15:
        final_result = (get_result(3, "fast", 0, 0)[0],) + \
                       (get_result(3, "fast", 0, 0)[1] % speed,) + get_result(3, "fast", 0, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "fast", 2, 0)[0],) + \
                       (get_result(3, "fast", 2, 0)[1] % speed,) + get_result(3, "fast", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估3：是否反弓
        # 计算右肩、右臀与垂直方向的夹角，应在8°-25°
        angle_of_upper_body = utils.get_angle_by_direction(pose_data_for_one, 12, 24, 1)
        if 8 <= angle_of_upper_body <= 25:
            final_result = (get_result(3, "body", 2, 0)[0],) + \
                           (get_result(3, "body", 2, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "body", 0, 0)[0],) + \
                           (get_result(3, "body", 0, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "body", 2, 0)[0],) + \
                       (get_result(3, "body", 2, 0)[1] % 10,) + get_result(3, "body", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估4：肩部发力
        # 计算距离的差值
        distance = get_distance_by_error_data(pose_data_for_one)
        if distance < 100:
            result_list.append(get_result(3, "hard", 2, 0))
        else:
            result_list.append(get_result(3, "hard", 0, 0))
    except NameError:
        result_list.append(get_result(3, "hard", 2, 0))

    try:
        # 评估5：折小臂
        # 右大臂与右小臂的夹角应在（90-120度）
        angle_between_arms = 180 - utils.get_angle_between_lines(pose_data_for_one, 12, 14, 14, 16)
        if 90 <= angle_between_arms <= 120:
            final_result = (get_result(3, "angle", 2, 0)[0],) + \
                           (get_result(3, "angle", 2, 0)[1] % angle_between_arms,) + get_result(3, "angle", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "angle", 0, 0)[0],) + \
                           (get_result(3, "angle", 0, 0)[1] % angle_between_arms,) + get_result(3, "angle", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "angle", 2, 0)[0],) + \
                       (get_result(3, "angle", 2, 0)[1] % 105,) + get_result(3, "angle", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估6：出手角度为45度
        # 右臂与水平方向的夹角
        angle_of_throw = utils.get_angle_by_direction(pose_data_for_one, 12, 16, 0)
        if angle_of_throw > 90:
            angle_of_throw = 180 - angle_of_throw
        # 出手角度处于30 - 60度都默认为47度
        if 30 <= angle_of_throw <= 60:
            result_list.append(get_result(3, "spin", 2, 0))
        elif angle_of_throw < 30:
            angle_of_throw = random.uniform(30, 44)
            final_result = (get_result(3, "spin", 0, 0)[0],) + (get_result(3, "spin", 0, 0)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 0)[2:5]
            result_list.append(final_result)
        else:
            angle_of_throw = random.uniform(50, 55)
            final_result = (get_result(3, "spin", 0, 1)[0],) + (get_result(3, "spin", 0, 1)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 1)[2:5]
            result_list.append(final_result)
    except NameError:
        angle_of_throw = 47
        result_list.append(get_result(3, "spin", 2, 0))

    # 评估7：投掷距离
    # 根据出手角度和出手速度进行计算。距离 = (出手速度^2 * sin(2*出手角度)) / 重力加速度
    gravity = 9.8  # 重力加速度
    radians = math.radians(angle_of_throw)  # 将角度转换为弧度
    distance = (speed ** 2 * math.sin(2 * radians)) / gravity
    if distance >= 30:
        final_result = (get_result(3, "distance", 2, 0)[0],) + \
                       (get_result(3, "distance", 2, 0)[1] % distance,) + get_result(3, "distance", 2, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "distance", 0, 0)[0],) + \
                       (get_result(3, "distance", 0, 0)[1] % distance,) + get_result(3, "distance", 0, 0)[2:5]
        result_list.append(final_result)

    return result_list

# ------------------------ 投准 -------------------------
def eval_throwDirect(person_id, pose_data_for_one):
    result_list = []

    try:
        # 评估1：肘部低于肩部
        # 比较右肘与右肩的垂直方向坐标，右肘不应低于右肩
        right_elbow_point_vertical_value = phase_identify.get_point(pose_data_for_one, 14)[1]
        right_shoulder_point_vertical_value = phase_identify.get_point(pose_data_for_one, 12)[1]
        print("right_elbow: ", right_elbow_point_vertical_value)
        print("right_shoulder: ", right_shoulder_point_vertical_value)
        if right_elbow_point_vertical_value <= right_shoulder_point_vertical_value:
            result_list.append(get_result(3, "height", 2, 0))
        else:
            result_list.append(get_result(3, "height", 0, 0))
    except NameError:
        result_list.append(get_result(3, "height", 2, 0))

    # 评估2：挥臂不快
    # 出手速度随机出，范围是16-21m/s，>=15m/s是标准
    speed = random.uniform(16, 21)
    if speed < 15:
        final_result = (get_result(3, "fast", 0, 0)[0],) + \
                       (get_result(3, "fast", 0, 0)[1] % speed,) + get_result(3, "fast", 0, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "fast", 2, 0)[0],) + \
                       (get_result(3, "fast", 2, 0)[1] % speed,) + get_result(3, "fast", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估3：是否反弓
        # 计算右肩、右臀与垂直方向的夹角，应在8°-25°
        angle_of_upper_body = utils.get_angle_by_direction(pose_data_for_one, 12, 24, 1)
        if 8 <= angle_of_upper_body <= 25:
            final_result = (get_result(3, "body", 2, 0)[0],) + \
                           (get_result(3, "body", 2, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "body", 0, 0)[0],) + \
                           (get_result(3, "body", 0, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "body", 2, 0)[0],) + \
                       (get_result(3, "body", 2, 0)[1] % 10,) + get_result(3, "body", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估4：肩部发力
        # 计算距离的差值
        distance = get_distance_by_error_data(pose_data_for_one)
        if distance < 100:
            result_list.append(get_result(3, "hard", 2, 0))
        else:
            result_list.append(get_result(3, "hard", 0, 0))
    except NameError:
        result_list.append(get_result(3, "hard", 2, 0))

    try:
        # 评估5：折小臂
        # 右大臂与右小臂的夹角应在（90度以上）
        angle_between_arms = 180 - utils.get_angle_between_lines(pose_data_for_one, 12, 14, 14, 16)
        if angle_between_arms >= 90:
            final_result = (get_result(3, "angle", 2, 0)[0],) + \
                           (get_result(3, "angle", 2, 0)[1] % angle_between_arms,) + get_result(3, "angle", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "angle", 0, 0)[0],) + \
                           (get_result(3, "angle", 0, 0)[1] % angle_between_arms,) + get_result(3, "angle", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "angle", 2, 0)[0],) + \
                       (get_result(3, "angle", 2, 0)[1] % 105,) + get_result(3, "angle", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估6：出手角度为45度
        # 右臂与水平方向的夹角
        angle_of_throw = utils.get_angle_by_direction(pose_data_for_one, 12, 16, 0)
        if angle_of_throw > 90:
            angle_of_throw = 180 - angle_of_throw
        # 出手角度处于30 - 60度都默认为47度
        if 30 <= angle_of_throw <= 60:
            result_list.append(get_result(3, "spin", 2, 0))
        elif angle_of_throw < 30:
            angle_of_throw = random.uniform(30, 44)
            final_result = (get_result(3, "spin", 0, 0)[0],) + (get_result(3, "spin", 0, 0)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 0)[2:5]
            result_list.append(final_result)
        else:
            angle_of_throw = random.uniform(50, 55)
            final_result = (get_result(3, "spin", 0, 1)[0],) + (get_result(3, "spin", 0, 1)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 1)[2:5]
            result_list.append(final_result)
    except NameError:
        angle_of_throw = 47
        result_list.append(get_result(3, "spin", 2, 0))

    # 评估7：投掷距离
    # 根据出手角度和出手速度进行计算。距离 = (出手速度^2 * sin(2*出手角度)) / 重力加速度
    gravity = 9.8  # 重力加速度
    radians = math.radians(angle_of_throw)  # 将角度转换为弧度
    distance = (speed ** 2 * math.sin(2 * radians)) / gravity
    if distance >= 30:
        final_result = (get_result(3, "distance", 2, 0)[0],) + \
                       (get_result(3, "distance", 2, 0)[1] % distance,) + get_result(3, "distance", 2, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "distance", 0, 0)[0],) + \
                       (get_result(3, "distance", 0, 0)[1] % distance,) + get_result(3, "distance", 0, 0)[2:5]
        result_list.append(final_result)

    return result_list

# ------------------------ 侧甩 -------------------------
def eval_sideThrow(person_id, pose_data_for_one):
    result_list = []

    try:
        # 评估1：肘部低于肩部
        # 比较右肘与右肩的垂直方向坐标，右肘不应低于右肩
        right_elbow_point_vertical_value = phase_identify.get_point(pose_data_for_one, 14)[1]
        right_shoulder_point_vertical_value = phase_identify.get_point(pose_data_for_one, 12)[1]
        # print("right_elbow: ", right_elbow_point_vertical_value)
        # print("right_shoulder: ", right_shoulder_point_vertical_value)
        distance = right_elbow_point_vertical_value - right_shoulder_point_vertical_value
        if distance < 30:
            result_list.append(get_result(3, "height", 2, 0))
        else:
            result_list.append(get_result(3, "height", 0, 0))
    except NameError:
        result_list.append(get_result(3, "height", 2, 0))

    # 评估2：挥臂不快
    # 出手速度随机出，范围是16-21m/s，>=15m/s是标准
    speed = random.uniform(16, 21)
    if speed < 15:
        final_result = (get_result(3, "fast", 0, 0)[0],) + \
                       (get_result(3, "fast", 0, 0)[1] % speed,) + get_result(3, "fast", 0, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "fast", 2, 0)[0],) + \
                       (get_result(3, "fast", 2, 0)[1] % speed,) + get_result(3, "fast", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估3：肩部发力
        # 计算距离的差值
        distance = get_distance_by_error_data(pose_data_for_one)
        if distance < 100:
            result_list.append(get_result(3, "hard", 2, 0))
        else:
            result_list.append(get_result(3, "hard", 0, 0))
    except NameError:
        result_list.append(get_result(3, "hard", 2, 0))

    try:
        # 评估4：折小臂
        # 右大臂与右小臂的夹角应在（60度以上）
        angle_between_arms = 180 - utils.get_angle_between_lines(pose_data_for_one, 12, 14, 14, 16)
        if angle_between_arms >= 60:
            final_result = (get_result(3, "angle", 2, 0)[0],) + \
                           (get_result(3, "angle", 2, 0)[1] % angle_between_arms,) + get_result(3, "angle", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "angle", 0, 0)[0],) + \
                           (get_result(3, "angle", 0, 0)[1] % angle_between_arms,) + get_result(3, "angle", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "angle", 2, 0)[0],) + \
                       (get_result(3, "angle", 2, 0)[1] % 105,) + get_result(3, "angle", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估5：出手角度为45度
        # 右臂与水平方向的夹角
        angle_of_throw = utils.get_angle_by_direction(pose_data_for_one, 12, 16, 0)
        if angle_of_throw > 90:
            angle_of_throw = 180 - angle_of_throw
        print(angle_of_throw)
        # 出手角度处于20 - 60度都默认为47度
        if 20 <= angle_of_throw <= 60:
            result_list.append(get_result(3, "spin", 2, 0))
        elif angle_of_throw < 20:
            angle_of_throw = random.uniform(30, 44)
            final_result = (get_result(3, "spin", 0, 0)[0],) + (get_result(3, "spin", 0, 0)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 0)[2:5]
            result_list.append(final_result)
        else:
            angle_of_throw = random.uniform(50, 55)
            final_result = (get_result(3, "spin", 0, 1)[0],) + (get_result(3, "spin", 0, 1)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 1)[2:5]
            result_list.append(final_result)
    except NameError:
        angle_of_throw = 47
        result_list.append(get_result(3, "spin", 2, 0))

    # 评估6：投掷距离
    # 根据出手角度和出手速度进行计算。距离 = (出手速度^2 * sin(2*出手角度)) / 重力加速度
    gravity = 9.8  # 重力加速度
    radians = math.radians(angle_of_throw)  # 将角度转换为弧度
    distance = (speed ** 2 * math.sin(2 * radians)) / gravity
    if distance >= 30:
        final_result = (get_result(3, "distance", 2, 0)[0],) + \
                       (get_result(3, "distance", 2, 0)[1] % distance,) + get_result(3, "distance", 2, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "distance", 0, 0)[0],) + \
                       (get_result(3, "distance", 0, 0)[1] % distance,) + get_result(3, "distance", 0, 0)[2:5]
        result_list.append(final_result)

    return result_list

# ------------------------ 滚手榴弹 -------------------------
def eval_roll(person_id, pose_data_for_one):
    result_list = []

    try:
        # 评估1：肘部高于肩部
        # 比较右肘与右肩的垂直方向坐标，右肘不应高于右肩
        right_elbow_point_vertical_value = phase_identify.get_point(pose_data_for_one, 3)[1]
        right_shoulder_point_vertical_value = phase_identify.get_point(pose_data_for_one, 2)[1]
        print("right_elbow: ", right_elbow_point_vertical_value)
        print("right_shoulder: ", right_shoulder_point_vertical_value)
        if right_elbow_point_vertical_value >= right_shoulder_point_vertical_value:
            result_list.append(get_result(3, "height", 2, 0))
        else:
            result_list.append(get_result(3, "height", 0, 0))
    except NameError:
        result_list.append(get_result(3, "height", 2, 0))

    # 评估2：挥臂不快
    # 出手速度随机出，范围是16-21m/s，>=15m/s是标准
    speed = random.uniform(16, 21)
    if speed < 15:
        final_result = (get_result(3, "fast", 0, 0)[0],) + \
                       (get_result(3, "fast", 0, 0)[1] % speed,) + get_result(3, "fast", 0, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "fast", 2, 0)[0],) + \
                       (get_result(3, "fast", 2, 0)[1] % speed,) + get_result(3, "fast", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估3：肩部发力
        # 计算距离的差值
        distance = get_distance_by_error_data(pose_data_for_one)
        if distance < 100:
            result_list.append(get_result(3, "hard", 2, 0))
        else:
            result_list.append(get_result(3, "hard", 0, 0))
    except NameError:
        result_list.append(get_result(3, "hard", 2, 0))

    try:
        # 评估4：折小臂
        # 右大臂与右小臂的夹角应在（90度以上）
        angle_between_arms = 180 - utils.get_angle_between_lines(pose_data_for_one, 12, 14, 14, 16)
        if angle_between_arms > 90:
            final_result = (get_result(3, "angle", 2, 0)[0],) + \
                           (get_result(3, "angle", 2, 0)[1] % angle_between_arms,) + get_result(3, "angle", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "angle", 0, 0)[0],) + \
                           (get_result(3, "angle", 0, 0)[1] % angle_between_arms,) + get_result(3, "angle", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "angle", 2, 0)[0],) + \
                       (get_result(3, "angle", 2, 0)[1] % 105,) + get_result(3, "angle", 2, 0)[2:5]
        result_list.append(final_result)

    return result_list

# ------------------------ 抛手榴弹 -------------------------
def eval_throw(person_id, pose_data_for_one):
    result_list = []

    try:
        # 评估1：右手高于头部
        # done
        right_hand_point_vertical_value = phase_identify.get_point(pose_data_for_one, 16)[1]
        head_point_vertical_value = phase_identify.get_point(pose_data_for_one, 0)[1]
        if right_hand_point_vertical_value < head_point_vertical_value:
            result_list.append(get_result(3, "height", 2, 0))
        else:
            result_list.append(get_result(3, "height", 0, 0))
    except NameError:
        result_list.append(get_result(3, "height", 2, 0))

    # 评估2：挥臂不快
    # 出手速度随机出，范围是16-21m/s，>=15m/s是标准
    speed = random.uniform(16, 21)
    if speed < 15:
        final_result = (get_result(3, "fast", 0, 0)[0],) + \
                       (get_result(3, "fast", 0, 0)[1] % speed,) + get_result(3, "fast", 0, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "fast", 2, 0)[0],) + \
                       (get_result(3, "fast", 2, 0)[1] % speed,) + get_result(3, "fast", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估3：是否反弓
        # 计算右肩、右臀与垂直方向的夹角，应在-10°~10°
        # done
        angle_of_upper_body = utils.get_angle_by_direction(pose_data_for_one, 12, 14, 1)
        if -10 <= angle_of_upper_body <= 10:
            final_result = (get_result(3, "body", 2, 0)[0],) + \
                           (get_result(3, "body", 2, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "body", 0, 0)[0],) + \
                           (get_result(3, "body", 0, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "body", 2, 0)[0],) + \
                       (get_result(3, "body", 2, 0)[1] % 10,) + get_result(3, "body", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估4：肩部发力
        # 计算距离的差值
        # no need to change
        distance = get_distance_by_error_data(pose_data_for_one)
        if distance < 100:
            result_list.append(get_result(3, "hard", 2, 0))
        else:
            result_list.append(get_result(3, "hard", 0, 0))
    except NameError:
        result_list.append(get_result(3, "hard", 2, 0))

    try:
        # 评估5：右手肘角度大于160
        # done
        right_elbow_angle = utils.get_angle_between_lines(pose_data_for_one, 14, 16, 14, 12)
        if right_elbow_angle >= 160:
            final_result = (get_result(3, "angle", 2, 0)[0],) + \
                           (get_result(3, "angle", 2, 0)[1] % right_elbow_angle,) + get_result(3, "angle", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "angle", 0, 0)[0],) + \
                           (get_result(3, "angle", 0, 0)[1] % right_elbow_angle,) + get_result(3, "angle", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "angle", 2, 0)[0],) + \
                       (get_result(3, "angle", 2, 0)[1] % 105,) + get_result(3, "angle", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估6：出手角度为90度
        # 右臂与水平方向的夹角
        # done?wtf ranndom?
        angle_of_throw = utils.get_angle_by_direction(pose_data_for_one, 14, 16, 0)
        if angle_of_throw > 90:
            angle_of_throw = 180 - angle_of_throw
        # 出手角度处于80~100度都默认为90度
        if 80 <= angle_of_throw <= 100:
            result_list.append(get_result(3, "spin", 2, 0))
        elif angle_of_throw < 80:
            angle_of_throw = random.uniform(80, 89)
            final_result = (get_result(3, "spin", 0, 0)[0],) + (get_result(3, "spin", 0, 0)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 0)[2:5]
            result_list.append(final_result)
        else:
            angle_of_throw = random.uniform(91, 100)
            final_result = (get_result(3, "spin", 0, 1)[0],) + (get_result(3, "spin", 0, 1)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 1)[2:5]
            result_list.append(final_result)
    except NameError:
        angle_of_throw = 87
        result_list.append(get_result(3, "spin", 2, 0))

    # 评估7：投掷距离
    # 根据出手角度和出手速度进行计算。距离 = (出手速度^2 * sin(2*出手角度)) / 重力加速度
    # no need to change 
    gravity = 9.8  # 重力加速度
    radians = math.radians(angle_of_throw)  # 将角度转换为弧度
    distance = (speed ** 2 * math.sin(2 * radians)) / gravity
    if distance >= 30:
        final_result = (get_result(3, "distance", 2, 0)[0],) + \
                       (get_result(3, "distance", 2, 0)[1] % distance,) + get_result(3, "distance", 2, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "distance", 0, 0)[0],) + \
                       (get_result(3, "distance", 0, 0)[1] % distance,) + get_result(3, "distance", 0, 0)[2:5]
        result_list.append(final_result)

    return result_list

# ------------------------ 塞手榴弹 -------------------------
def eval_stuff(person_id, pose_data_for_one):
    result_list = []

    try:
        # 评估1：手部高于头部或低于胯
        right_hand_point_vertical_value = phase_identify.get_point(pose_data_for_one, 16)[1]
        head_point_vertical_value = phase_identify.get_point(pose_data_for_one, 0)[1]
        leg_point_vertical_value = phase_identify.get_point(pose_data_for_one, 24)[1]
        if right_hand_point_vertical_value <= head_point_vertical_value or right_hand_point_vertical_value >= leg_point_vertical_value:
            result_list.append(get_result(3, "height", 2, 0))
        else:
            result_list.append(get_result(3, "height", 0, 0))
    except NameError:
        result_list.append(get_result(3, "height", 2, 0))

    # 评估2：挥臂不快
    # 出手速度随机出，范围是16-21m/s，>=15m/s是标准
    speed = random.uniform(16, 21)
    if speed < 15:
        final_result = (get_result(3, "fast", 0, 0)[0],) + \
                       (get_result(3, "fast", 0, 0)[1] % speed,) + get_result(3, "fast", 0, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "fast", 2, 0)[0],) + \
                       (get_result(3, "fast", 2, 0)[1] % speed,) + get_result(3, "fast", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估3：是否反弓
        # 计算右肩、右臀与垂直方向的夹角，应在8°-25°
        angle_of_upper_body = utils.get_angle_by_direction(pose_data_for_one, 12, 14, 1)
        if 0 <= angle_of_upper_body <= 10:
            final_result = (get_result(3, "body", 2, 0)[0],) + \
                           (get_result(3, "body", 2, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "body", 0, 0)[0],) + \
                           (get_result(3, "body", 0, 0)[1] % angle_of_upper_body,) + get_result(3, "body", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "body", 2, 0)[0],) + \
                       (get_result(3, "body", 2, 0)[1] % 10,) + get_result(3, "body", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估4：肩部发力
        # 计算距离的差值
        distance = get_distance_by_error_data(pose_data_for_one)
        if distance < 100:
            result_list.append(get_result(3, "hard", 2, 0))
        else:
            result_list.append(get_result(3, "hard", 0, 0))
    except NameError:
        result_list.append(get_result(3, "hard", 2, 0))

    try:
        # 评估5：折小臂
        # 右大臂与右小臂的夹角应在（80-180度）
        angle_between_arms = utils.get_angle_between_lines(pose_data_for_one, 14, 12, 14, 16)
        if 90 <= angle_between_arms <= 80:
            final_result = (get_result(3, "angle", 2, 0)[0],) + \
                           (get_result(3, "angle", 2, 0)[1] % angle_between_arms,) + get_result(3, "angle", 2, 0)[2:5]
            result_list.append(final_result)
        else:
            final_result = (get_result(3, "angle", 0, 0)[0],) + \
                           (get_result(3, "angle", 0, 0)[1] % angle_between_arms,) + get_result(3, "angle", 0, 0)[2:5]
            result_list.append(final_result)
    except NameError:
        final_result = (get_result(3, "angle", 2, 0)[0],) + \
                       (get_result(3, "angle", 2, 0)[1] % 105,) + get_result(3, "angle", 2, 0)[2:5]
        result_list.append(final_result)

    try:
        # 评估6：出手角度为45度
        # 右臂与水平方向的夹角
        angle_of_throw = utils.get_angle_by_direction(pose_data_for_one, 14, 16, 0)
        if angle_of_throw > 90:
            angle_of_throw = 180 - angle_of_throw
        # 出手角度处于30 - 60度都默认为47度
        if -45 <= angle_of_throw <= 45:
            result_list.append(get_result(3, "spin", 2, 0))
        elif angle_of_throw < -45:
            angle_of_throw = random.uniform(-90, -45)
            final_result = (get_result(3, "spin", 0, 0)[0],) + (get_result(3, "spin", 0, 0)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 0)[2:5]
            result_list.append(final_result)
        else:
            angle_of_throw = random.uniform(45, 90)
            final_result = (get_result(3, "spin", 0, 1)[0],) + (get_result(3, "spin", 0, 1)[1] % angle_of_throw,) + \
                           get_result(3, "spin", 0, 1)[2:5]
            result_list.append(final_result)
    except NameError:
        angle_of_throw = 47
        result_list.append(get_result(3, "spin", 2, 0))

    # 评估7：投掷距离
    # 根据出手角度和出手速度进行计算。距离 = (出手速度^2 * sin(2*出手角度)) / 重力加速度
    gravity = 9.8  # 重力加速度
    radians = math.radians(angle_of_throw)  # 将角度转换为弧度
    distance = (speed ** 2 * math.sin(2 * radians)) / gravity
    if distance >= 30:
        final_result = (get_result(3, "distance", 2, 0)[0],) + \
                       (get_result(3, "distance", 2, 0)[1] % distance,) + get_result(3, "distance", 2, 0)[2:5]
        result_list.append(final_result)
    else:
        final_result = (get_result(3, "distance", 0, 0)[0],) + \
                       (get_result(3, "distance", 0, 0)[1] % distance,) + get_result(3, "distance", 0, 0)[2:5]
        result_list.append(final_result)

    return result_list

def eval_squat(pose_data_for_one):
    result_list = []
    try:
        # 评估1：检测是否下蹲
        # 臀、左膝盖、左脚踝小于80度
        angle_between_thighs = 180 - utils.get_angle_between_lines(pose_data_for_one, 12, 13, 13, 14)
        if angle_between_thighs < 80:
            result_list.append(get_result(4, "action", 2, 0))
        else:
            result_list.append(get_result(4, "action", 0, 0))
    except NameError:
        result_list.append(get_result(4, "action", 2, 0))

    return result_list


def eval_coherence(pose_data_for_one):
    # 评估1：动作是否连续（全返回动作标准）
    result_list = [get_result(5, "coherence", 2, 0)]
    return result_list


def eval_default():
    return [(-1, "", ["", ], ["", ], ""), ]


def get_evaluation(person_id, pos_data_for_one, action_id, algo_type):
    """
    返回 [<state, result, [suggestion_list], [video_url_list], reason>,...]
    """
    result_list = []

    # 0609变更: 仅对投阶段进行评估
    # 场景类型：
    # 1. 投远 => algo_type = 4
    # 2. 投准 => algo_type = 5
    # 3. 侧甩 => algo_type = 0
    # 4. 滚手榴弹 => algo_type = 1
    # 5. 抛手榴弹 => algo_type = 2
    # 6. 塞手榴弹 => algo_type = 3

    # 默认类型：投远
    if algo_type == 4:
        print("Use algo_type = 4")
        if action_id == 3:  # 投
            result_list = eval_throwFar(person_id, pos_data_for_one)
        else:
            result_list = eval_default()
        return result_list
    # 算法：投准
    elif algo_type == 5:
        print("Use algo_type = 5")
        if action_id == 3:  # 投
            result_list = eval_throwDirect(person_id, pos_data_for_one)
        else:
            result_list = eval_default()
        return result_list
    # 算法：侧甩
    elif algo_type == 0:
        print("Use algo_type = 0")
        if action_id == 3:  # 投
            result_list = eval_sideThrow(person_id, pos_data_for_one)
        else:
            result_list = eval_default()
        return result_list
    # 算法：滚手榴弹
    elif algo_type == 1:
        print("Use algo_type = 1")
        if action_id == 3:  # 投
            result_list = eval_roll(person_id, pos_data_for_one)
        else:
            result_list = eval_default()
        return result_list
    # 算法：抛手榴弹
    elif algo_type == 2:
        print("Use algo_type = 2")
        if action_id == 3:  # 投
            result_list = eval_throw(person_id, pos_data_for_one)
        else:
            result_list = eval_default()
        return result_list
    # 算法：塞手榴弹
    elif algo_type == 3:
        print("Use algo_type = 3")
        if action_id == 2:  # 塞
            result_list = eval_stuff(person_id, pos_data_for_one)
        else:
            result_list = eval_default()
        return result_list


    # if action_id == 0:  # 准备
    #     pass
    # elif action_id == 1:  # 拉
    #     result_list = eval_pull(pos_data_for_one)
    # elif action_id == 2:  # 引
    #     result_list = eval_stretch(pos_data_for_one)
    # elif action_id == 3:  # 投
    #     result_list = eval_throw(person_id, pos_data_for_one)
    # elif action_id == 4:  # 蹲
    #     result_list = eval_squat(pos_data_for_one)
    # else:  # 连贯
    #     result_list = eval_coherence(pos_data_for_one)
    # return result_list
