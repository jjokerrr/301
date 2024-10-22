import json
from Config.db_config import conn, cursor, write_eval_sql, write_advice_sql, get_begin_group_id_sql


def get_begin_group_id():
    cursor.execute(get_begin_group_id_sql)
    group_id = cursor.fetchone()[0]
    if group_id is None:
        group_id = 1
    print('begin_group_id:', group_id)
    conn.commit()
    return group_id


def write_eval_and_advice_data_to_db(eval_data, advice_data, group_id, algo_type):
    print("write eval to db", eval_data)
    cursor.executemany(write_eval_sql, eval_data)
    to_write_advice = []
    for i in range(len(advice_data)):
        if advice_data[i]:
            to_write_advice.append((group_id, i, json.dumps(advice_data[i], ensure_ascii=False), algo_type))
    print('write advice to db', advice_data)
    cursor.executemany(write_advice_sql, to_write_advice)
    conn.commit()


def process_eval_data(queue):
    group_id = get_begin_group_id()
    eval_data = []
    advice_data = [[] for i in range(3)]
    while True:
        person_id, action_id, result, algo_type = queue.get()
        # print(person_id, action_id, result)
        if person_id == -1 and action_id == -1 and result is None:
            print("detect frame with nobody")
            if not eval_data:
                continue
            # 新批次，此时将上一批次数据写入数据库
            print("write advice and eval data to mysql, enter next group")
            write_eval_and_advice_data_to_db(eval_data, advice_data, group_id, algo_type)
            eval_data = [] 
            advice_data = [[] for i in range(3)]
            group_id += 1
        print("评估数据")
        print((person_id, action_id, result))
        if not result:
            continue
        action_eval = []
        for res in result:
            action_eval.append({"state": res[0], "eval_result": res[1]})
            advice_data[person_id].append({"eval_result": res[1], "advice": res[2], "video_url": res[3], "reason": res[4], "state": res[0]})
        eval_data.append((group_id, person_id, action_id, json.dumps(action_eval, ensure_ascii=False)))

