"""
测试 InfluxDB 3 的各种查询操作
验证哪些操作支持，哪些不支持
"""

from influxdb_client_3 import InfluxDBClient3

client = InfluxDBClient3(
    host="http://localhost:8181",
    token="apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ",
    database="concaxu"
)

def test_query(description, query):
    """测试查询并打印结果"""
    print(f"\n🔍 测试: {description}")
    print(f"SQL: {query}")
    try:
        result = client.query(query)
        print(f"✅ 成功: {result}")
    except Exception as e:
        print(f"❌ 失败: {e}")

# 基础查询测试
print("=" * 60)
print("🚀 InfluxDB 3 查询功能测试")
print("=" * 60)

# 1. 基础操作
test_query("查看所有表", "SHOW TABLES")
test_query("查看数据库", "SHOW DATABASES")

# 2. 计数操作
test_query("COUNT(*) 计数", "SELECT COUNT(*) FROM sensor_data")
test_query("COUNT(字段) 计数", "SELECT COUNT(temperature) FROM sensor_data")

# 3. 基础查询
test_query("查询前10条", "SELECT * FROM sensor_data LIMIT 10")
test_query("查询特定字段", "SELECT device_id, temperature FROM sensor_data LIMIT 5")

# 4. 聚合函数
test_query("AVG 平均值", "SELECT AVG(temperature) FROM sensor_data")
test_query("MAX 最大值", "SELECT MAX(temperature) FROM sensor_data")
test_query("MIN 最小值", "SELECT MIN(temperature) FROM sensor_data")
test_query("SUM 求和", "SELECT SUM(temperature) FROM sensor_data")

# 5. 分组查询
test_query("GROUP BY 分组", "SELECT device_id, COUNT(*) FROM sensor_data GROUP BY device_id")
test_query("GROUP BY + AVG", "SELECT device_id, AVG(temperature) FROM sensor_data GROUP BY device_id")

# 6. 时间相关查询
test_query("查询时间字段", "SELECT time FROM sensor_data LIMIT 5")
test_query("按时间排序", "SELECT * FROM sensor_data ORDER BY time DESC LIMIT 5")
test_query("时间范围查询", "SELECT * FROM sensor_data WHERE time >= now() - INTERVAL '1 hour' LIMIT 5")

# 7. 条件查询
test_query("WHERE 条件", "SELECT * FROM sensor_data WHERE device_id = 'device001' LIMIT 5")
test_query("WHERE 数值条件", "SELECT * FROM sensor_data WHERE temperature > 25 LIMIT 5")

# 8. 时间窗口聚合（可能不支持）
test_query("时间分桶", "SELECT time_bucket(INTERVAL '5 minutes', time) as bucket, AVG(temperature) FROM sensor_data GROUP BY bucket")

# 9. 标准差（可能不支持）
test_query("STDDEV 标准差", "SELECT STDDEV(temperature) FROM sensor_data")

# 10. CASE WHEN（可能不支持）
test_query("CASE WHEN", """
SELECT device_id, temperature,
CASE 
    WHEN temperature > 30 THEN 'HIGH'
    WHEN temperature < 20 THEN 'LOW'
    ELSE 'NORMAL'
END as temp_level
FROM sensor_data LIMIT 5
""")

print("\n" + "=" * 60)
print("🎯 测试完成！")
print("=" * 60)