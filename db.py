import mysql.connector
from datetime import datetime, timedelta

# MySQL 연결 설정
conn = mysql.connector.connect(
    host="energiology-db.crg0yqic8dx6.ap-northeast-2.rds.amazonaws.com",
    user="root",
    password="capstoneaplus!!",
    database="dev"
)
cursor = conn.cursor()

# 시작 시간 설정 (2024년 5월 1일 00:00:00)
start_time = datetime(2024, 5, 6, 0, 0, 0)

# 00:00부터 23:59까지 반복
for hour in range(24):
    for minute in range(60):
        current_time = start_time + timedelta(hours=hour, minutes=minute)
        # 각 포트에 대한 데이터 생성
        for port_id in range(1, 6):
            query = """
                INSERT INTO dev.power (port_id, power_usage, power_prediction_usage, power_cost, power_prediction_cost, time, power_supplier)
                VALUES ({}, null, {}, null, {}, '{}', null)
            """.format(port_id, 5 * (port_id), 100 * (port_id), current_time.strftime('%Y-%m-%d %H:%M:%S'))
            cursor.execute(query)
    print("hour",hour)

# 변경사항 저장 및 연결 종료
conn.commit()
conn.close()
