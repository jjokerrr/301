import os
import sys
import time

from process_eval_data import process_eval_data
from process_img_data import process_img_data
from multiprocessing import Process, Queue, Value
from multiprocessing import Manager
from flask import Flask, request
from mediapipe_stream import rtmp_start
from time import sleep
import ctypes
import re


image_in_queue, image_and_action_out_queue, evaluation_and_suggestion_out_queue = Queue(), Queue(), Queue()
flag = Value('b', False)
algo_type = Value('i',0)
push_url = Manager().Value(ctypes.c_char_p, "")

def is_valid_pushurl(pushurl):
    # 正则表达式匹配IPv4
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    # 正则表达式匹配完整的URL
    pattern = r'^rtmp://' + ipv4_pattern + r'/live/pushstream$'
    
    # 使用re.match来检查字符串是否匹配正则表达式
    if re.match(pattern, pushurl):
        return True
    else:
        return False

def chang_to_rtmp(url):
    return 'rtmp://'+ url + '/live/pushstream'

def run_flask_app(flag, algo_type):
    """由于现场服务器环境问题，只能将Flask应用包装在一个函数里以进程方式启动"""
    app = Flask(__name__)

    @app.route('/control', methods=["GET", "POST"])
    def control_flag():
        """控制评估的开始与结束"""
        c_flag = int(request.args.get('control_flag'))
        c_algo_type = int(request.args.get('algo_type'))
        # 如果传递过来的flag为1且当前flag为False，开启评估
        if c_flag and not flag.value:
            # 获取该组评估人数
            people_num = int(request.args.get('people_num'))
            image_in_queue.put(("start", people_num, c_algo_type))
            flag.value = not flag.value
            algo_type.value = c_algo_type
            return make_response(200, "Flag changed to START. People num: " + str(people_num) + ", algo type: " + str(algo_type))
        # 如果传递过来的flag为0且当前flag为True，结束一组评估
        if not c_flag and flag.value:
            flag.value = not flag.value
            algo_type.value = c_algo_type
            # 停滞0.1秒，在实时流不再写入队列后再将标志信息写入队列
            time.sleep(0.1)
            print('send end singal')
            image_in_queue.put(("end", None, None))
            return make_response(200, "Flag changed to END")
        return make_response(200, "Nothing changed")

    @app.route('/control/discard', methods=["GET", "POST"])
    def discard():
        """丢弃当前评估，并将flag置成False，停止评估"""
        if flag.value:
            flag.value = not flag.value
            # 停滞0.1秒，在实时流不再写入队列后再将标志信息写入队列
            time.sleep(0.1)
            image_in_queue.put(("discard", None, None))
            return make_response(200, "Current evaluation is discarded")
        return make_response(200, "Currently there is no evaluation running.")
    
    @app.route('/control/pushurl', methods=["GET"])
    def getPushUrl():
        """从前端获取推流地址，推流地址写wsl的ip地址
            请求参数： push_url   推流地址
        """
        url = request.args.get('push_url')
        if len(url) <= 0 or not is_valid_pushurl(chang_to_rtmp(url)):
            make_response(400, 'illegel push_url, please check your push_url, push_url formate: rtmp://ip/live/pushstream')
        push_url.value = chang_to_rtmp(url)
        return make_response(200, "get push_url, current push_url is " + push_url.value)

    def make_response(code, msg):
        return {
            "code": code,
            "data": msg
        }

    app.run(host="0.0.0.0", port=5001)


dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../')
from algo import start

if __name__ == '__main__':
    algo_process = Process(target=start, args=(image_in_queue, image_and_action_out_queue,
                                               evaluation_and_suggestion_out_queue))

    eval_process = Process(target=process_eval_data, args=(evaluation_and_suggestion_out_queue,),
                           daemon=True)
    img_process = Process(target=process_img_data, args=(image_and_action_out_queue,),
                          daemon=True)

    print("eval")
    eval_process.start()
    print("img")
    img_process.start()
    print("algo")
    algo_process.start()
    print("server")
    flask_process = Process(target=run_flask_app, args=(flag, algo_type))
    flask_process.start()
    print("rtmp")
    while True: 
        if is_valid_pushurl(push_url.value):
            break
        # print('push_url :'+ push_url.value)
    print('rtmp push url:' , push_url.value)
    print('rtmp start')
    rtmp_start(image_in_queue, flag, algo_type, push_url.value)
