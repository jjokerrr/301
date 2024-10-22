import re
from datetime import datetime
import flask
from flask import Flask, request
import json
import pymysql
from Config.db_config import conn, cursor
import os
import subprocess

app = Flask(__name__)
get_eval_sql = 'select result from eval_tb where group_id = %s and person_id = %s and action_id = %s'
get_video_sql = 'select video_path from video_tb where group_id = %s and person_id = %s and action_id = %s'
get_advice_sql = 'select advice from advice_tb where algo_type = %s order by id desc limit 1'
get_phy_sql = 'select * from phy_tb where device_id = %s order by ts desc limit '
write_phy_sql = 'insert into phy_tb (`device_id`, `hr`, `br`, `spo2`, `pr`, `ts`) ' \
                'values (%s, %s, %s, %s, %s, %s)'
get_device_by_person_sql = 'select device_id from bind_tb where group_id = %s and person_id = %s ' \
                           'order by id desc limit 1'
get_device_list_sql = 'select * from device_tb order by id'
write_bind_sql = 'insert into bind_tb (`device_id`, `group_id`, `person_id`, `person_name`) ' \
                 'values (%s, %s, %s, %s)'
delete_bind_relation_sql = 'delete from bind_tb where person_id = %s and group_id = %s'
get_group_list_sql = 'select distinct(group_id) from advice_tb'
write_person_sql = 'insert into person_tb (`person_id`, `person_name`, `device_id`, `device_batch`, `project_type`, ' \
                   '`update_time`, `group_id`) values (%s, %s, %s, %s, %s, %s, %s)'
get_person_mes_sql = 'select * from person_tb where person_id = %s and project_type = %s order by id'
update_person_sql = 'update person_tb set person_name = %s, device_id = %s, device_batch = %s, update_time = %s,' \
                    ' group_id = %s where person_id = %s and project_type = %s'
delete_person_sql = 'delete from person_tb where person_id = %s and project_type = %s'
search_person_page_sql = 'select * from person_tb order by id desc limit %s, %s'
search_person_page_by_type_sql_left = 'select * from person_tb where '
search_person_page_by_type_sql_right = ' = %s order by id desc limit %s, %s'
search_person_page_by_name_sql_right = ' like %s order by id desc limit %s, %s'


@app.route('/getAdvice')
def get_advice():  # put application's code here
    group_id = request.args.get('group_id')
    person_id = request.args.get('person_id')
    algo_type = request.args.get('algo_type')
    if group_id is None or person_id is None:
        return make_response(400, "group_id 和 person_id不能为空")
    if not group_id.isnumeric() or not person_id.isnumeric():
        return make_response(400, "group_id 和 person_id必须为数字")
    conn.ping()
    cursor.execute(get_advice_sql % (algo_type))
    result = cursor.fetchone()
    if result is None:
        return make_response(404, "无数据")
    result = result[0]
    response = dict()
    response["group_id"] = group_id
    response["person_id"] = person_id
    response["result"] = []
    action_result = dict()
    action_result["key"] = "action"
    action_result["value"] = []
    action_result["solution"] = []
    action_result["state"] = []
    action_result["video_url"] = []
    action_result["reason"] = []
    for res in json.loads(result):
        action_result["state"].append(res["state"])
        action_result["value"].append(res["eval_result"])
        action_result["solution"].append(res["advice"])
        action_result["video_url"].append(res["video_url"])
        action_result["reason"].append(res["reason"])
    response["result"].append(action_result)
    print(response)
    conn.commit()
    return make_response(200, json.dumps(response, ensure_ascii=False))


@app.route('/get_throw_data')
def get_throw_data():  # put application's code here
    def regex_throw_data(string):
        # 获取“出手角度为”这5个字后的紧邻的数字，要求算法提供的数据必须保留至2位小数，否则无法识别
        angle_pattern = r"出手角度为(\d+\.\d{2})"
        speed_pattern = r"出手速度为(\d+\.\d{2})"
        distance_pattern = r"投掷距离为(\d+\.\d{2})"

        match = re.search(angle_pattern, string)
        if match:
            response["angle"] = float(match.group(1))
            print("出手角度:", response["angle"])
        match = re.search(speed_pattern, string)
        if match:
            response["speed"] = float(match.group(1))
            print("出手速度:", response["speed"])
        match = re.search(distance_pattern, string)
        if match:
            response["distance"] = float(match.group(1))
            print("投掷距离:", response["distance"])

    group_id = request.args.get('group_id')
    person_id = request.args.get('person_id')
    if group_id is None or person_id is None:
        return make_response(400, "group_id 和 person_id不能为空")
    if not group_id.isnumeric() or not person_id.isnumeric():
        return make_response(400, "group_id 和 person_id必须为数字")
    conn.ping()
    # 投掷数据只有阶段3才有
    cursor.execute(get_eval_sql % (group_id, person_id, 3))
    result = cursor.fetchone()
    conn.commit()
    if result is None:
        return make_response(404, "无数据")
    result = result[0]
    response = dict()
    response["angle"] = 0.0
    response["speed"] = 0.0
    response["distance"] = 0.0
    for res in json.loads(result):
        regex_throw_data(res["eval_result"])
    return make_response(200, json.dumps(response, ensure_ascii=False))


@app.route('/getEval')
def get_eval():  # put application's code here
    group_id = request.args.get('group_id')
    person_id = request.args.get('person_id')
    action_id = request.args.get('action_id')
    if group_id is None or person_id is None or action_id is None:
        return make_response(400, "group_id, person_id, action_id不能为空")
    if not group_id.isnumeric() or not person_id.isnumeric() or not action_id.isnumeric():
        return make_response(400, "group_id, person_id, action_id必须为数字")
    conn.ping()
    cursor.execute(get_eval_sql % (group_id, person_id, action_id))
    result = cursor.fetchone()
    if result is None:
        return make_response(404, "无数据")
    result = result[0]
    response = dict()
    response["group_id"] = group_id
    response["person_id"] = person_id
    response["action_id"] = action_id
    response["result"] = []
    action_result = dict()
    action_result["key"] = "action"
    action_result["value"] = []
    action_result["state"] = []
    for res in json.loads(result):
        action_result["value"].append(res["eval_result"])
        action_result["state"].append(res["state"])
    response["result"].append(action_result)
    print(response)
    conn.commit()
    return make_response(200, json.dumps(response, ensure_ascii=False))


def make_response(code, response):
    response = flask.make_response(response)
    response.status_code = code
    return response


@app.route('/getVideo')
def get_video():  # put application's code here
    group_id = request.args.get('group_id')
    person_id = request.args.get('person_id')
    action_id = request.args.get('action_id')
    if group_id is None or person_id is None or action_id is None:
        return make_response(400, "group_id, person_id, action_id不能为空")
    if not group_id.isnumeric() or not person_id.isnumeric() or not action_id.isnumeric():
        return make_response(400, "group_id, person_id, action_id必须为数字")
    conn.ping()
    cursor.execute(get_video_sql % (group_id, person_id, action_id))
    result = cursor.fetchone()
    if result is None:
        return make_response(404, "无数据")
    url = result[0]
    print(url)
    return make_response(200, url)


def make_code_desc(code, desc):
    return {
        "code": code,
        "description": desc,
    }


def get_phy_from_db(group_id, person_id, time_interval):
    print(f'get device from db, group_id: {group_id}, person_id: {person_id}')
    cursor.execute(get_device_by_person_sql, (group_id, person_id))
    device_id = ""
    for d in cursor.fetchall():
        device_id = d[0]
    if device_id == "":
        return {}
    print("get phy from db, device_id: ", device_id)
    conn.ping()
    cursor.execute(get_phy_sql + time_interval, device_id)
    phy_data = []
    i = 0
    hr_sum = 0
    br_sum = 0
    hr_svg = 0
    br_svg = 0
    for d in cursor.fetchall():
        cell = {}
        cell["device_id"] = d[1]
        cell["hr"] = d[2]
        cell["br"] = d[3]
        cell["spo2"] = d[4]
        cell["pr"] = d[5]
        cell["timestamp"] = d[6].strftime('%Y-%m-%d %H:%M:%S')
        cell["group_id"] = group_id
        cell["person_id"] = person_id
        phy_data.append(cell)
        hr_sum += float(d[2])
        br_sum += float(d[3])
        i += 1
    # print(phy_data)
    conn.commit()
    if len(phy_data) == 0:
        return {}
    if i != 0:
        hr_svg = hr_sum / i
        br_svg = br_sum / i
    hr_eval = "绿" if hr_svg < 100 else ("黄" if hr_svg <= 130 else "红")
    br_eval = "绿" if br_svg < 25 else ("黄" if br_svg <= 50 else "红")
    hr_eval_desc = "心理状态良好" if hr_eval == "绿" else ("心理状态紧张" if hr_eval == "黄" else "心理状态欠佳")
    br_eval_desc = "心理状态良好" if br_eval == "绿" else ("心理状态紧张" if br_eval == "黄" else "心理状态欠佳")
    res = {
        "phy_data": phy_data,
        "eval_hr": hr_eval,
        "eval_hr_desc": hr_eval_desc,
        "eval_br": br_eval,
        "eval_br_desc": br_eval_desc,
    }
    conn.commit()
    return res


def write_phy_to_db(data):
    print("write phy to db, data: ", data)
    conn.ping()
    cursor.execute(write_phy_sql, data)
    conn.commit()


def get_device_list_from_db():
    print("get device list from db")
    conn.ping()
    cursor.execute(get_device_list_sql)
    device_list = []
    for d in cursor.fetchall():
        device_list.append(d[1])
    conn.commit()
    return device_list


def bind_person_device_to_db(data):
    print("write bind to db, data: ", data)
    conn.ping()
    cursor.executemany(write_bind_sql, data)
    conn.commit()


def delete_bind_relation_from_db(data):
    print("delete bind relation from db, data: ", data)
    conn.ping()
    cursor.execute(delete_bind_relation_sql, data)
    conn.commit()


def get_group_list_from_db():
    print("get group list from db")
    conn.ping()
    cursor.execute(get_group_list_sql)
    group_list = []
    for d in cursor.fetchall():
        # print(d)
        group_list.append(d[0])
    conn.commit()
    return group_list


def write_person_mes_to_db(data):
    print("write person message to db, data: ", data)
    conn.ping()
    cursor.execute(write_person_sql, data)
    conn.commit()


def update_person_mes_to_db(data):
    print("update person message to db, data: ", data)
    conn.ping()
    cursor.execute(update_person_sql, data)
    conn.commit()


def delete_person_mes_to_db(data):
    print("delete person message to db, data: ", data)
    conn.ping()
    cursor.execute(delete_person_sql, data)
    conn.commit()


def get_person_mes_from_db(person_id, project_type):
    print("get person mes from db")
    parmes = (person_id, project_type)
    conn.ping()
    cursor.execute(get_person_mes_sql, parmes)
    person_mes = []
    for d in cursor.fetchall():
        cell = {}
        cell["person_id"] = d[1]
        cell["person_name"] = d[2]
        cell["device_id"] = d[3]
        cell["device_batch"] = d[4]
        cell["project_type"] = d[5]
        cell["update_time"] = d[6].strftime('%Y-%m-%d %H:%M:%S')
        person_mes.append(cell)
    conn.commit()
    return person_mes


def search_person_page(sql, params):
    print("search person page from db")
    # print(sql)
    conn.ping()
    cursor.execute(sql, params)
    person_mes = []
    for d in cursor.fetchall():
        # print(d)
        cell = {}
        cell["person_id"] = d[1]
        cell["person_name"] = d[2]
        cell["device_id"] = d[3]
        cell["device_batch"] = d[4]
        cell["project_type"] = d[5]
        cell["update_time"] = d[6].strftime('%Y-%m-%d %H:%M:%S')
        cell["group_id"] = d[7]
        person_mes.append(cell)
    conn.commit()
    return person_mes


@app.route('/get_phy', methods=["GET", "POST"])
def get_phy():
    group_id = request.args.get('group_id')
    person_id = request.args.get('person_id')
    time_interval = request.args.get('time_interval')
    if group_id is None or person_id is None or time_interval is None:
        return {
            "code": 400,
            "description": "group_id, person_id, time_interval 不能为空",
        }
    if not group_id.isnumeric() or not person_id.isnumeric() or not time_interval.isnumeric():
        return {
            "code": 400,
            "description": "group_id, person_id, time_interval 必须为数字",
        }
    conn.ping()
    phy_data = get_phy_from_db(group_id, person_id, time_interval)
    return {
        "code": 200,
        "description": "ok",
        "data": phy_data
    }


@app.route('/get_device_list', methods=["GET", "POST"])
def get_device_list():
    device_list = get_device_list_from_db()
    return {
        "code": 200,
        "description": "ok",
        "data": device_list
    }


@app.route('/bind_person_device', methods=["POST"])
def bind_person_device():
    request_data = request.get_json()
    # print(request_data["data"])
    data = request_data["data"]
    bind_data = []
    for cell in data:
        device_id = cell.get("device_id")
        group_id = cell.get("group_id")
        person_id = cell.get("person_id")
        if device_id is None or group_id is None or person_id is None or cell.get("person_name") is None:
            return {
                "code": 400,
                "description": "device_id, group_id, person_id, person_name 不能为空",
            }
        if not group_id.isnumeric() or not person_id.isnumeric():
            return {
                "code": 400,
                "description": "group_id, person_id必须为数字",
            }
        bind_data.append((cell["device_id"], cell["group_id"], cell["person_id"], cell["person_name"]))
    bind_person_device_to_db(bind_data)
    return {
        "code": 200,
        "description": "ok",
    }


@app.route('/delete_bind_relation', methods=["DELETE"])
def delete_bind_relation():
    person_id = request.args.get('person_id')
    group_id = request.args.get('group_id')
    if person_id is None or group_id is None:
        return make_code_desc(400, "person_id, group_id 不能为空")
    if not person_id.isnumeric() or not group_id.isnumeric():
        return make_code_desc(400, "person_id, group_id 必须为数字")
    bind_relation = (person_id, group_id)
    delete_bind_relation_from_db(bind_relation)
    return {
        "code": 200,
        "description": "ok",
    }


@app.route('/get_group_list', methods=["GET", "POST"])
def get_group_list():
    group_list = get_group_list_from_db()
    print(group_list)
    return {
        "code": 200,
        "description": "ok",
        "data": {
            "group_list": group_list,
            "count": len(group_list)
        }
    } 


@app.route('/person/create', methods=["POST"])
def create_person_mes():
    request_data = request.get_json()
    data = request_data.get("data")
    # print(data)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    person_id = data.get("person_id")
    person_name = data.get("person_name")
    device_id = data.get("device_id")
    device_batch = data.get("device_batch")
    project_type = data.get("project_type")
    group_id = data.get("group_id")
    if person_id is None or person_name is None or device_id is None or device_batch is None \
            or project_type is None or group_id is None:
        return make_code_desc(400, "person_id, person_name, device_id, device_batch, project_type, group_id 不能为空")
    if not device_batch.isnumeric() or not project_type.isnumeric() or not group_id.isnumeric():
        return make_code_desc(400, "device_batch, project_type, group_id 必须为数字")
    if len(get_person_mes_from_db(person_id, project_type)) != 0:
        return make_code_desc(400, "用户已存在，请前往修改")
    person_mes = (person_id, person_name, device_id, device_batch, project_type, current_time, group_id)
    write_person_mes_to_db(person_mes)
    return make_code_desc(200, "ok")


@app.route('/person/update', methods=["POST"])
def update_person_mes():
    request_data = request.get_json()
    data = request_data.get("data")
    # print(data)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    person_id = data.get("person_id")
    person_name = data.get("person_name")
    device_id = data.get("device_id")
    device_batch = data.get("device_batch")
    project_type = data.get("project_type")
    group_id = data.get("group_id")
    if person_id is None or person_name is None or device_id is None or device_batch is None \
            or project_type is None or group_id is None:
        return make_code_desc(400, "person_id, person_name, device_id, device_batch, project_type, group_id 不能为空")
    if not device_batch.isnumeric() or not project_type.isnumeric() or not group_id.isnumeric():
        return make_code_desc(400, "device_batch, project_type, group_id 必须为数字")
    if len(get_person_mes_from_db(person_id, project_type)) == 0:
        return make_code_desc(400, "用户不存在，请前往创建")
    person_mes = (person_name, device_id, device_batch, current_time, group_id, person_id, project_type)
    update_person_mes_to_db(person_mes)
    return make_code_desc(200, "ok")


@app.route('/person/delete', methods=["DELETE"])
def delete_person_mes():
    person_id = request.args.get('person_id')
    project_type = request.args.get('project_type')
    if person_id is None or project_type is None:
        return make_code_desc(400, "person_id, project_type 不能为空")
    if not project_type.isnumeric():
        return make_code_desc(400, "project_type 必须为数字")
    person_list = person_id.split("@")
    for pid in person_list:
        if len(get_person_mes_from_db(pid, project_type)) == 0:
            return make_code_desc(400, "用户不存在，请前往创建")
        person_mes = (pid, project_type)
        delete_person_mes_to_db(person_mes)
    return make_code_desc(200, "ok")


@app.route('/person/get', methods=["GET"])
def get_person_mes():
    search_type = request.args.get('search_type')
    search_value = request.args.get('search_value')
    page_num = request.args.get('page_num')
    page_size = request.args.get('page_size')
    if page_num is None or page_size is None:
        return make_code_desc(400, "page_num, page_size 不能为空")
    if search_type is None or search_type == "":
        offset = (int(page_num) - 1) * int(page_size)
        search_params = (offset, int(page_size))
        print(search_params)
        search_res = search_person_page(search_person_page_sql, search_params)
        return {
            "code": 200,
            "description": "ok",
            "data": search_res
        }
    offset = (int(page_num) - 1) * int(page_size)
    search_params = (search_value, offset, int(page_size))
    if search_type == "person_name":
        search_params = ('%' + search_value + '%', offset, int(page_size))
        search_sql = search_person_page_by_type_sql_left + search_type + search_person_page_by_name_sql_right
    else:
        search_sql = search_person_page_by_type_sql_left + search_type + search_person_page_by_type_sql_right
    search_res = search_person_page(search_sql, search_params)
    return {
        "code": 200,
        "description": "ok",
        "data": search_res
    }


@app.route('/restart_server', methods=["GET"])
def restart_server():
    return {
        "code": 200,
        "description": "ok",
    }



if __name__ == '__main__':
    app.run(host='0.0.0.0')
    # print(search_person_page((0, 10)))
