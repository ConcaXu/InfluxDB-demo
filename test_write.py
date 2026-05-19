"""
简单测试：验证 InfluxDB 3 批量写入
"""
import time
from influxdb_client_3 import InfluxDBClient3

client = InfluxDBClient3(
    host="http://localhost:8181",
    token="apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ",
    database="concaxu"
)

print("测试 1：写入单条数据")
base_ts = int(time.time() * 1_000_000_000)
record1 = f"test_data,device=dev1 value=100 {base_ts}"
print(f"  记录: {record1}")
client.write(record=record1)
print("  ✅ 成功\n")

print("测试 2：写入 3 条数据（换行符分隔的字符串）")
records = [
    f"test_data,device=dev2 value=200 {base_ts + 1000}",
    f"test_data,device=dev3 value=300 {base_ts + 2000}",
    f"test_data,device=dev4 value=400 {base_ts + 3000}",
]
records_str = "\n".join(records)
print(f"  记录:\n{records_str}")
client.write(record=records_str)
print("  ✅ 成功\n")

print("测试 3：查询验证")
result = client.query("SELECT * FROM test_data")
print(f"  结果:\n{result}\n")

count_result = client.query("SELECT COUNT(*) FROM test_data")
print(f"  总数:\n{count_result}")
