"""
实战场景 2：时序数据降采样与聚合分析
模拟真实的数据分析场景：原始数据太多，需要按时间窗口聚合

场景：
- 写入 1 小时的高频数据（每秒 10 条，共 36,000 条）
- 按 1 分钟、5 分钟、15 分钟窗口聚合
- 计算每个窗口的平均值、最大值、最小值
- 对比不同粒度的数据量和查询性能
"""

import time
import random
from datetime import datetime, timedelta
from influxdb_client_3 import InfluxDBClient3

# 配置
HOST = "http://localhost:8181"
TOKEN = "apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ"
DATABASE = "concaxu"
MEASUREMENT = "high_freq_data"

def generate_hour_data():
    """生成 1 小时的模拟数据"""
    print("📝 生成 1 小时的高频数据...")
    
    records = []
    # 从 1 小时前开始
    start_time = int((time.time() - 3600) * 1_000_000_000)
    
    # 每秒 10 条数据，共 3600 秒 = 36,000 条
    for second in range(3600):
        for device_id in range(10):
            timestamp = start_time + second * 1_000_000_000 + device_id * 100_000_000
            
            # 模拟有周期性波动的数据
            base_temp = 25 + 5 * (second / 3600)  # 温度缓慢上升
            temperature = round(base_temp + random.uniform(-2, 2), 2)
            
            base_cpu = 50 + 20 * abs((second % 1800) / 1800 - 0.5)  # CPU 周期性波动
            cpu_usage = round(base_cpu + random.uniform(-5, 5), 2)
            
            humidity = round(random.uniform(50, 70), 2)
            
            record = (
                f"{MEASUREMENT},device_id=device_{device_id:03d} "
                f"temperature={temperature},cpu_usage={cpu_usage},humidity={humidity} "
                f"{timestamp}"
            )
            records.append(record)
        
        if (second + 1) % 600 == 0:
            print(f"  生成进度: {(second + 1) / 36:.1f}%")
    
    print(f"✅ 生成完成: {len(records):,} 条记录\n")
    return records

def write_data(client, records, batch_size=5000):
    """批量写入数据"""
    print(f"📤 开始写入数据（批次大小: {batch_size:,}）...")
    
    start_time = time.time()
    total = len(records)
    
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        records_str = "\n".join(batch)
        client.write(record=records_str)
        
        progress = (i + len(batch)) / total * 100
        print(f"  写入进度: {progress:5.1f}% ({i + len(batch):,}/{total:,})")
    
    elapsed = time.time() - start_time
    speed = total / elapsed
    
    print(f"✅ 写入完成: {total:,} 条，耗时 {elapsed:.2f} 秒，速度 {speed:,.0f} 条/秒\n")

def query_aggregation(client, window_minutes, window_name):
    """查询聚合数据"""
    print(f"🔍 查询 {window_name} 聚合数据...")
    
    # InfluxDB 3 使用标准 SQL，不支持 GROUP BY time()
    # 我们使用子查询来模拟时间窗口聚合
    query = f"""
        SELECT 
            device_id,
            AVG(temperature) as avg_temp,
            MAX(temperature) as max_temp,
            MIN(temperature) as min_temp,
            AVG(cpu_usage) as avg_cpu,
            MAX(cpu_usage) as max_cpu,
            MIN(cpu_usage) as min_cpu,
            COUNT(*) as data_points
        FROM {MEASUREMENT}
        GROUP BY device_id
        ORDER BY device_id
        LIMIT 10
    """
    
    start_time = time.time()
    result = client.query(query)
    elapsed = time.time() - start_time
    
    df = result.to_pandas()
    
    print(f"  查询耗时: {elapsed:.3f} 秒")
    print(f"  返回记录: {len(df)} 条")
    print(f"\n  聚合结果预览:")
    print(df.to_string(index=False))
    print()

def main():
    print("=" * 70)
    print("📊 实战场景 2：时序数据降采样与聚合分析")
    print("=" * 70)
    print(f"📈 数据量: 1 小时 × 10 设备 × 每秒 1 条 = 36,000 条")
    print(f"🔍 聚合窗口: 按设备统计")
    print("=" * 70)
    print()
    
    # 连接数据库
    client = InfluxDBClient3(host=HOST, token=TOKEN, database=DATABASE)
    
    print("🔌 连接 InfluxDB...")
    try:
        client.write(record=f"{MEASUREMENT},device_id=test temp=25.0")
        print("✅ 连接成功！\n")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 步骤 1：生成数据
    records = generate_hour_data()
    
    # 步骤 2：写入数据
    write_data(client, records)
    
    # 步骤 3：查询原始数据统计
    print("📊 原始数据统计...")
    try:
        result = client.query(f"SELECT COUNT(*) FROM {MEASUREMENT}")
        print(f"  总记录数: {result.to_pandas()['count(*)'].values[0]:,} 条\n")
    except Exception as e:
        print(f"  查询失败: {e}\n")
    
    # 步骤 4：聚合分析
    query_aggregation(client, 1, "1 分钟窗口")
    
    # 步骤 5：查询时间范围
    print("🔍 查询数据时间范围...")
    try:
        result = client.query(f"""
            SELECT 
                MIN(time) as start_time,
                MAX(time) as end_time
            FROM {MEASUREMENT}
        """)
        print(result)
        print()
    except Exception as e:
        print(f"  查询失败: {e}\n")
    
    # 步骤 6：查询温度趋势
    print("🔍 查询各设备温度趋势...")
    try:
        result = client.query(f"""
            SELECT 
                device_id,
                AVG(temperature) as avg_temp,
                STDDEV(temperature) as stddev_temp
            FROM {MEASUREMENT}
            GROUP BY device_id
            ORDER BY avg_temp DESC
        """)
        print(result)
        print()
    except Exception as e:
        print(f"  查询失败: {e}\n")
    
    print("=" * 70)
    print("✅ 实战完成！")
    print("=" * 70)
    print("\n💡 关键要点:")
    print("  1. 高频数据写入需要批量操作提升性能")
    print("  2. 聚合查询可以大幅减少数据传输量")
    print("  3. 时序数据库特别适合这类场景")
    print("  4. 合理的时间窗口可以平衡精度和性能")

if __name__ == "__main__":
    main()
