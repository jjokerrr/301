from Config.db_config import conn, cursor, get_begin_group_id_sql, write_video_sql
import cv2

fps = 10.0
target_size = (640, 480)
video_dir = './videos/'


def resize_and_pad(img, target_size, pad_color=0):
    try:
        old_size = img.shape[0:2]
        # 计算原始图像宽高与目标图像大小的比例，并取其中的较小值
        ratio = min(float(target_size[i]) / (old_size[i]) for i in range(len(old_size)))
        # 根据上边求得的比例计算在保持比例前提下得到的图像大小
        new_size = tuple([int(i * ratio) for i in old_size])
        # 根据上边的大小进行放缩
        img = cv2.resize(img, (new_size[1], new_size[0]))
        # 计算需要填充的像素数目（图像的宽这一维度上）
        pad_w = target_size[1] - new_size[1]
        # 计算需要填充的像素数目（图像的高这一维度上）
        pad_h = target_size[0] - new_size[0]
        top, bottom = pad_h // 2, pad_h - (pad_h // 2)
        left, right = pad_w // 2, pad_w - (pad_w // 2)
        # 使用指定的颜色对图像进行填充
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=pad_color)
    except:
        print("process_img_data error")
    return img


def get_begin_group_id():
    cursor.execute(get_begin_group_id_sql)
    group_id_list = cursor.fetchone()
    if group_id_list is None:
        return 1
    group_id = group_id_list[0]
    if group_id is None:
        group_id = 1
    print('begin_group_id:', group_id)
    conn.commit()
    return group_id


def write_video_path_to_db(video_path_url_list, group_id):
    cursor.executemany(write_video_sql, video_path_url_list)
    conn.commit()
    print('wrote to db, group_id:', group_id)

def process_img_data(queue):
    group_id = get_begin_group_id()
    to_write_flag = False
    video_path_url_list = []
    video_writers = {}
    overall_video_writers = {}
    while True:
        person_id, action_id, img = queue.get()
        # print(person_id, action_id, img)
        if person_id == -1 and action_id == -1 and img is None:
            # 如果没有要写的数据则跳过
            if not to_write_flag:
                continue
            # 将url写入db
            print('write to db')
            write_video_path_to_db(video_path_url_list, group_id)
            # 将url_list重置为空list
            video_path_url_list = []
            # 释放video writer， 重置writers为空dict
            for video_writer in video_writers.values():
                video_writer.release()
            video_writers = {}
            overall_video_writers = {}
            # 已经写完了，将flag改回False
            to_write_flag = False
            group_id += 1

        # 阶段5和阶段0不做写入
        if img is None or action_id == 5 or action_id == 0:
            continue

        # 将图片填充至640x480
        img = resize_and_pad(img, target_size, pad_color=[255, 0, 0])
        video_path = video_dir + str(group_id) + str(person_id) + str(action_id) + '.mp4'
        print('video_path', video_path)
        if video_path not in video_writers.keys():
            video_writers[video_path] = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps,(640, 480))
            # video_url格式实例: /videos/1101.mp4
            video_path_url_list.append((group_id, person_id, action_id, video_path[1:]))
        if person_id not in overall_video_writers.keys():
            # 整体流程视频视为阶段5
            overall_video_path = video_dir + str(group_id) + str(person_id) + str(5) + '.mp4'
            overall_video_writers[person_id] = cv2.VideoWriter(overall_video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps,
                                                               (640, 480))
            video_path_url_list.append((group_id, person_id, 5, overall_video_path[1:]))
        video_writer = video_writers[video_path]
        overall_video_writer = overall_video_writers[person_id]
        overall_video_writer.write(img)
        video_writer.write(img)

        # 修改写入flag
        to_write_flag = True
