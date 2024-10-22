import pymysql


conn = pymysql.connect(host='172.22.192.1', user='root', port=3306, password='admin@123456', db='pose_data', charset="utf8")
cursor = conn.cursor()
write_eval_sql = 'REPLACE INTO eval_tb (`group_id`, `person_id`, `action_id`, `result`) VALUES (%s, %s, %s, %s)'
write_video_sql = 'REPLACE INTO video_tb (`group_id`, `person_id`, `action_id`, `video_path`) VALUES (%s, %s, %s, %s)'
write_advice_sql = 'REPLACE INTO advice_tb (`group_id`, `person_id`, `advice`, `algo_type`) VALUES (%s, %s, %s, %s)'
get_begin_group_id_sql = 'SELECT MAX(group_id) + 1 FROM eval_tb'
