import multiprocessing
from multiprocessing import Process, Queue
# import processor


# 从后端获取一帧图片数据
def get_one_frame_data(queue):
    """
    获取一帧的数据，包括经过openpose处理的json对象数据和含骨架的图片
    """
    openpose_result, processed_image, algo_type = queue.get()  # 如果队列中没有消息会阻塞
    return openpose_result, processed_image, algo_type


# 给后端输送图片切割和阶段划分的结果
def put_cut_image_and_action_result(cut_image_and_action_result_queue, data):
    """
    data:(personID, actionID, img)
    """
    # put data into queue
    cut_image_and_action_result_queue.put(data)


# 给后端输送评估和建议的结果
def put_evaluation_and_suggestion_result(evaluation_and_suggestion_result_queue, data):
    """
    data:(personID, actionID, (state, result, suggestion))
    """
    # put data into queue
    evaluation_and_suggestion_result_queue.put(data)


# 模拟后端的调用方式
# def __mock_backend_call():
#
#     q = Queue()
#     p = Process(target=processor.start, args=(q, q, q))
#
#     p.start()
#
#
#
#     q.put('ocean')
#     q.put('forest')
#     q.put('land')
#     # 由于在队列管道里只存储了3个指，当取到第四个的时候会发生阻塞，导致程序一直不会结束，等待接收值
#
#
# if __name__ == '__main__':
#     __mock_backend_call()
