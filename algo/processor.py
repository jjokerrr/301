from multiprocessing import Process, Queue
import handler
import image_cut
import phase_identify
import recognize_persons
import utils
import evaluator

pre_action_id = [-1 for i in range(10)]
eval_data = [None for j in range(10)]
person_num = 0
abnormal_frame = 0
# algo type => 评估场景，0-5代表总共6个场景，默认为0
algo_type = 0


def is_data_valid(data):
    if data is None:
        return False
    for d in data:
        if d is None:
            return False
    return True


def convert_data_item(item, width, height):
    res = []
    for i in item:
        # print(i)
        res.append([i['x'] * width, i['y'] * height])
    return res


def convert_data(data, width, height):
    res = []
    for d in data:
        res.append(convert_data_item(d, width, height))
    return res


# 处理正常帧
def do_normal_work(data, img, image_and_action_out_queue, evaluation_and_suggestion_out_queue):
    print("enter do_normal_work")
    key_points, boxes = recognize_persons.parse(data)
    # print(person_num)
    # print(boxes)
    for id in range(person_num):
        # print("person_num = ", person_num)
        new_axis_left_top = utils.swap_x_and_y(boxes[id][0])
        new_axis_right_bottom = utils.swap_x_and_y(boxes[id][1])

        cut_img = image_cut.cut(img, new_axis_left_top, new_axis_right_bottom)
        action_id = phase_identify.identify_single_person(id, key_points[id], algo_type)
        print(action_id)
        handler.put_cut_image_and_action_result(image_and_action_out_queue, (id, action_id, cut_img))

        # pre_action_id阶段已结束，判断并发送该阶段评估结果
        if pre_action_id[id] != action_id:
            if (0 < pre_action_id[id] < 5 and eval_data[id] is not None) or pre_action_id[id] == 5:
                # 获得评估数据，其中algo_type为场景号，为0-5
                res2 = evaluator.get_evaluation(id, eval_data[id], pre_action_id[id], algo_type)
                print(res2)
                handler.put_evaluation_and_suggestion_result(evaluation_and_suggestion_out_queue,
                                                            (id, pre_action_id[id], res2, algo_type))
        # 返回action_id阶段中，与标准动作差异最小的数据
        eval_data[id] = evaluator.get_min_distance_data(id, key_points[id], pre_action_id[id], action_id)
        pre_action_id[id] = action_id


# 检测当前组是否结束
def check_whether_this_group_is_end():
    return abnormal_frame >= 120


def reset_group_ending_check_process():
    global abnormal_frame
    abnormal_frame = 0


# 处理异常帧
def do_abnormal_work():
    global abnormal_frame
    print("enter do_abnormal_work")
    abnormal_frame += 1

    # 将剩余的评估数据写入队列
    # for id in range(person_num):
    #     if (0 < pre_action_id[id] < 5 and eval_data[id] is not None) or pre_action_id[id] == 5:
    #         res2 = evaluator.get_evaluation(id, eval_data[id], pre_action_id[id])
    #         handler.put_evaluation_and_suggestion_result(evaluation_and_suggestion_out_queue,
    #                                                      (id, pre_action_id[id], res2))
    #     pre_action_id[id] = -1
    #     eval_data[id] = None
    #
    # # 给后端发送标记,是否有必要？？？
    # handler.put_cut_image_and_action_result(image_and_action_out_queue, (-1, -1, None))
    # handler.put_evaluation_and_suggestion_result(evaluation_and_suggestion_out_queue, (-1, -1, None))


# 做阶段开始标志到来时的相关处理工作
def do_pre_work(param, algo):
    global person_num, algo_type
    person_num = param
    algo_type = algo
    print("enter do_pre_work")


# 做阶段结束标志出现后的相关处理工作
def do_post_work(image_and_action_out_queue, evaluation_and_suggestion_out_queue):
    print("enter do_post_work")
    phase_identify.reset()
    # 将剩余的评估数据写入队列
    for id in range(person_num):
        if (0 < pre_action_id[id] < 5 and eval_data[id] is not None) or pre_action_id[id] == 5:
            res2 = evaluator.get_evaluation(id, eval_data[id], pre_action_id[id], algo_type)
            handler.put_evaluation_and_suggestion_result(evaluation_and_suggestion_out_queue,
                                                         (id, pre_action_id[id], res2, algo_type))
        pre_action_id[id] = -1
        eval_data[id] = None

    # 给后端发送标记
    handler.put_cut_image_and_action_result(image_and_action_out_queue, (-1, -1, None))
    handler.put_evaluation_and_suggestion_result(evaluation_and_suggestion_out_queue, (-1, -1, None, algo_type))
    print("post work done.")


def start(image_in_queue, image_and_action_out_queue, evaluation_and_suggestion_out_queue):
    global pre_action_id, person_num, eval_data

    while True:
        param1, param2, param3 = handler.get_one_frame_data(image_in_queue)  # 阻塞调用，如果queue中没有数据的话, param3表示算法类型
        # print(param1, param2)
        if type(param1) == str:  # 从队列中取出控制信息
            if param1 == "start":  # 开始评估
                do_pre_work(param2, param3)
            elif param1 == "end":  # 结束评估
                do_post_work(image_and_action_out_queue, evaluation_and_suggestion_out_queue)
            continue
        # 从队列中取出openpose数据和图片信息
        data, img = param1, param2  # data就是[results.pose_landmarks.landmark]，有可能为None，左上为原点,x为横比例
        # print(data)

        if is_data_valid(data):  # 正常的阶段划分、裁剪和评估
            data = convert_data(data, img.shape[1], img.shape[0])
            do_normal_work(data, img, image_and_action_out_queue, evaluation_and_suggestion_out_queue)
        else:
            do_abnormal_work()

        if check_whether_this_group_is_end():  # 同end标识，结束当前组的评估
            reset_group_ending_check_process()
            # do_pre_work(1)  # 人数固定为1人
            do_post_work(image_and_action_out_queue, evaluation_and_suggestion_out_queue)
