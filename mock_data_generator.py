import os
import json
import numpy as np

import cv2
from mediapipe_process import PoseEstimator

# generate mock data as:
# videos => videos with landmarks drew on videos, used for displaying on frontend.
# images => images with landmarks & standard action data on specific algo type.

# Parameters
# src: Source file of procession.
# src_type: Which types of source needs to process, support on "image" and "video"
# algo_type: Which algo type the source file belongs to, which will be functioned at the naming of output files.
# action_stage (Optional): Which action stage the source file belongs to, which will be functioned at the naming of output files. If input is video type then this parameter should be None.

# 场景类型：
    # 1. 投远 => algo_type = 4
    # 2. 投准 => algo_type = 5
    # 3. 侧甩 => algo_type = 0
    # 4. 滚手榴弹 => algo_type = 1
    # 5. 抛手榴弹 => algo_type = 2
    # 6. 塞手榴弹 => algo_type = 3
algo_dict = {
    0: "sideThrow",
    1: "roll",
    2: "throw",
    3: "stuff",
    4: "throwFar",
    5: "throwDirect"
}

phase_dict = {
    "拉": 1,
    "引": 2,
    "投": 3,
    "塞": 2
}

def generate_img_mock_data(img_path, output_folder, algo_type, if_batch_inference = False):
    pose_estimator = PoseEstimator()
    # if true, then path is a folder.
    if if_batch_inference and os.path.isdir(img_path):
        for file in os.listdir(img_path):
            img = cv2.imread(os.path.join(img_path, file))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = pose_estimator.process(img)
            pose_estimator.draw_landmarks(img, results)
            img.flags.writeable = True
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            # save output image
            filename = file.split(".")[0] + "_pose.jpg"
            cv2.imwrite(os.path.join(img_path, filename), img)
            print("Image Save done, " + filename)
            # generate standard data
            standard = {}
            count = 0
            for landmark in results.pose_landmarks.landmark:
                standard[str(count)] = [landmark.x, landmark.y, landmark.visibility]
                count += 1
            # save standard data
            standard_data_filename = "standard_data_" + str(phase_dict[file.split(".")[0]]) + ".json"
            with open(os.path.join(output_folder, algo_dict[algo_type], standard_data_filename), "w+") as f:
                f.write(json.dumps(standard))
            print("Standard data save successful, " + standard_data_filename)


def generate_vid_mock_data(vid_path, if_black):
    pose_estimator = PoseEstimator()
    cap = cv2.VideoCapture(vid_path)
    # 获取视频的宽度
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    # 获取视频的高度
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # save processed video as mp4.
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 设置编码格式为 mp4
    if if_black:
        output_file = vid_path.split(".")[0] + "_pose_black.mp4"
    else:
        output_file = vid_path.split(".")[0] + "_pose.mp4"
    out = cv2.VideoWriter(output_file, fourcc, cap.get(cv2.CAP_PROP_FPS), (width, height))
    while cap.isOpened():
        success, img = cap.read()
        if not success:
            print("Reach the end")
            break
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose_estimator.process(img)
        if if_black:
            black_img = np.zeros_like(img)
            pose_estimator.draw_landmarks(black_img, results)
            black_img.flags.writeable = True
            black_img = cv2.cvtColor(black_img, cv2.COLOR_RGB2BGR)
            out.write(black_img)
        else:
            pose_estimator.draw_landmarks(img, results)
            img.flags.writeable = True
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            out.write(img)
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("Process video done, " + output_file)


def mock_data_finetune(data_base):
    for key, value in algo_dict.items():
        data_dir = os.path.join(data_base, value)
        for file in os.listdir(data_dir):
            if file.endswith("_fixed.json"):
                continue
            filename = file.split('.')[0] + "_2560*1440_fixed.json"
            with open(os.path.join(data_dir, file), "r+") as f:
                lst = json.loads(f.read())
            for k, v in lst.items():
                v[0] = v[0] * 2560
                v[1] = v[1] * 1440
            with open(os.path.join(data_dir, filename), "w+") as f:
                f.write(json.dumps(lst))
            print(f"{filename} done.")
            

if __name__ == "__main__":
    # ------------------------------- Tune input data config in this block ----------------------------
    basedir = "/home/tzo/301_24/backend"
    vid_file = "videos/0000.mp4"
    img_file = "imgs/"
    # if needs to do batch inference then use the image_folder
    # 场景类型：
    # 1. 投远 => algo_type = 4
    # 2. 投准 => algo_type = 5
    # 3. 侧甩 => algo_type = 0
    # 4. 滚手榴弹 => algo_type = 1
    # 5. 抛手榴弹 => algo_type = 2
    # 6. 塞手榴弹 => algo_type = 3
    algo_type = 0   
    image_folder = "imgs/" + algo_dict[algo_type]
    output_folder = os.path.join(basedir, "algo/mock_data")
    # if needs batch inference.
    if_batch_inference = True
    # -------------------------------------------- End of block ---------------------------------------

    # ------------------------------------- Tune parameters in this block -----------------------------
    src_vid = os.path.join(basedir, vid_file)
    src_img = os.path.join(basedir, img_file)
    src_img_dir = os.path.join(basedir, image_folder)
    src_type = "video"
    action_stage = None
    if_black = True
    # -------------------------------------------- End of block ---------------------------------------
    # if src_type == "video":
    #     generate_vid_mock_data(src_vid, if_black)
    # elif src_type == "image":
    #     generate_img_mock_data(src_img_dir, output_folder, algo_type, if_batch_inference)
    mock_data_finetune(output_folder)
