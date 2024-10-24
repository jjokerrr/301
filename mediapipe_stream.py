# This is a sample Python script.
import platform
import subprocess
from time import sleep

import cv2
from mediapipe_process import PoseEstimator

pull_url_list = ['/home/tzo/301_24/backend/videos/0000.mp4',
            '/home/tzo/301_24/backend/videos/0001.mp4',
            '/home/tzo/301_24/backend/videos/0002.mp4',
            '/home/tzo/301_24/backend/videos/0003.mp4',
            '/home/tzo/301_24/backend/videos/0004.mp4',
            '/home/tzo/301_24/backend/videos/0005.mp4']

push_url = 'rtmp://172.30.64.1/live/pushstream'
ffmpeg_win_path = '/usr/bin/ffmpeg'
ffmpeg_linux_path = 'ffmpeg'


def rtmp_start(image_in_queue, flag, algo_type):
    # 读取的rtmp数据流
    

    if platform.system().lower() == 'windows':
        ffmpeg_path = ffmpeg_win_path
    elif platform.system().lower() == 'linux':
        ffmpeg_path = ffmpeg_linux_path

    pull_url = pull_url_list[algo_type.value]
    while True:
        # 使用FFmpeg检查RTMP流状态
        cmd = [ffmpeg_path, '-i', pull_url]
        result = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = result.stderr.read().decode('utf-8')

        # 检查输出中是否包含"Connection refused"字符串
        if 'Connection refused' not in output:
            print("RTMP流已开启")
            break

        print("等待RTMP流开启...")
        # 等待一段时间再继续尝试
        cv2.waitKey(2000)  # 等待2秒

    # 初始化态势感知器
    pose_estimator = PoseEstimator()
    
    
    # 从pull_url抓取视频对象
    

    # 产生一个推流pipe，推送到push_url上
    command = [ffmpeg_path,
                '-y', '-an',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', '1920*1080',
                '-r', '10',
                '-i', '-',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-f', 'flv',
                push_url]
    
    pipe = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE)

    sleep(1)
    while True:
        if flag.value:
            pull_url = pull_url_list[algo_type.value]
            print('compute start, current pull url : ' + pull_url)
            cap = cv2.VideoCapture(pull_url)
            ret = cap.grab()
            while flag.value:
                ret, image = cap.retrieve()
                if not ret:
                    print('fail to retrieve image')
                    continue
                # 经过姿态估计处理
                image.flags.writeable = False
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = pose_estimator.process(img=image)
                pose_estimator.draw_landmarks(image, results)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                # Flip the image horizontally for a selfie-view display.
                # cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
                
                # 推流
                
                # print("img.tostring(): ", image.tostring())
                try:
                    pipe.stdin.write(image.tobytes())
                    # pipe.stdin.write(image.tostring())
                except BrokenPipeError as e:
                    print(f"Error writing to pipe: {e}")
                    # pipe.terminate()
                    # 创建新管道
                    # pipe = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE)
                    break
                except Exception as e: 
                    print(f"Error: {e}")
                    break
                # print("image:", image)

                if image is None or image.size == 0:
                    print("Empty image data")
                    continue

                landmarks = []
                # mediapipe的landmark类无法序列化，因此需要我们自己封装
                # 空帧传回None
                if results.pose_landmarks:
                    for landmark in results.pose_landmarks.landmark:
                        landmarks.append({"x": landmark.x, "y": landmark.y, "visibility": landmark.visibility})
                    # 算法那边需要这样的格式：[第一个人的信息]
                    landmarks = [landmarks]
                else:
                    landmarks = None
                # print(landmarks)
                image_in_queue.put((landmarks, image, None))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                ret = cap.grab()
                if not ret:
                    cap = cv2.VideoCapture(pull_url)
                    ret = cap.grab()
            # pipe.terminate()
            print("compute down, current flag: "+ str(flag.value) + ", current pull_url: " + pull_url)
            cap.release()
        else :
            sleep(1)
            print("waiting start....")
    print("end")
    cv2.destroyAllWindows()
    cap.release()
