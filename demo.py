from influxdb_client_3 import InfluxDBClient3

client = InfluxDBClient3(
    host="http://localhost:8181",
    token="apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ",
    database="concaxu"
)

table = client.query("SHOW TABLES")
# ✅ 写入一条数据
client.write(
    record="sensor_data,device_id=device001 temperature=25.6,humidity=62"
)
print(table)