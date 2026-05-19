"""
实战场景 1：实时监控告警系统
模拟真实的 IoT 设备监控，当指标异常时触发告警

场景：
- 10 个传感器设备实时上报数据
- 温度超过 30°C 触发高温告警
- CPU 使用率超过 80% 触发性能告警
- 湿度低于 45% 触发干燥告警
- 每秒写入一批数据，持续监控 60 秒
"""

import time
import random
from datetime import datetime
from influxdb_client_3 import InfluxDBClient3

# 配置
HOST = "http://localhost:8181"
TOKEN = "apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ"
DATABASE = "concaxu"
MEASUREMENT = "realtime_monitor"

# 告警阈值
TEMP_HIGH = 30.0
CPU_HIGH = 80.0
HUMIDITY_LOW = 45.0

# 告警统计
alert_stats = {
    "high_temp": 0,
    "high_cpu": 0,
    "low_humidity": 0
}

def generate_realtime_data(device_id: int, timestamp: int):
    """生成实时数据，有一定概率产生异常值"""
    # 80% 正常数据，20% 异常数据
    is_anomaly = random.random() < 0.2
    
    if is_anomaly:
        temperature = round(random.uniform(28.0, 35.0), 2)  # 可能超标
        cpu_usage = round(random.uniform(70.0, 95.0), 2)    # 可能超标
        humidity = round(random.uniform(35.0, 50.0), 2)     # 可能过低
    else:
        temperature = round(random.uniform(20.0, 28.0), 2)
        cpu_usage = round(random.uniform(30.0, 70.0), 2)
        humidity = round(random.uniform(50.0, 80.0), 2)
    
    mem_usage = round(random.uniform(40.0, 85.0), 2)
    
    return {
        "device_id": f"sensor_{device_id:03d}",
        "temperature": temperature,
        "humidity": humidity,
        "cpu_usage": cpu_usage,
        "mem_usage": mem_usage,
        "timestamp": timestamp
    }

def check_alerts(data):
    """检查告警条件"""
    alerts = []
    
    if data["temperature"] > TEMP_HIGH:
        alerts.append(f"🔥 高温告警: {data['temperature']}°C")
        alert_stats["high_temp"] += 1
    
    if data["cpu_usage"] > CPU_HIGH:
        alerts.append(f"⚠️  CPU告警: {data['cpu_usage']}%")
        alert_stats["high_cpu"] += 1
    
    if data["humidity"] < HUMIDITY_LOW:
        alerts.append(f"💧 湿度告警: {data['humidity']}%")
        alert_stats["low_humidity"] += 1
    
    return alerts

def main():
    print("=" * 70)
    print("🚨 实战场景 1：实时监控告警系统")
    print("=" * 70)
    print(f"📊 监控设备: 10 个传感器")
    print(f"⏱️  监控时长: 60 秒")
    print(f"📡 采样频率: 每秒 1 次")
    print(f"🔥 高温阈值: > {TEMP_HIGH}°C")
    print(f"⚠️  CPU阈值: > {CPU_HIGH}%")
    print(f"💧 湿度阈值: < {HUMIDITY_LOW}%")
    print("=" * 70)
    
    # 连接数据库
    client = InfluxDBClient3(host=HOST, token=TOKEN, database=DATABASE)
    
    print("\n🔌 连接 InfluxDB...")
    try:
        client.write(record=f"{MEASUREMENT},device_id=test temp=25.0")
        print("✅ 连接成功！\n")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    print("🚀 开始实时监控...\n")
    
    total_records = 0
    total_alerts = 0
    
    try:
        for second in range(1, 61):  # 监控 60 秒
            batch_records = []
            batch_alerts = []
            
            # 每秒采集 10 个设备的数据
            base_timestamp = int(time.time() * 1_000_000_000)
            
            for device_id in range(10):
                data = generate_realtime_data(device_id, base_timestamp + device_id * 1000)
                
                # 检查告警
                alerts = check_alerts(data)
                if alerts:
                    batch_alerts.append((data["device_id"], alerts))
                    total_alerts += len(alerts)
                
                # 构造 Line Protocol
                record = (
                    f"{MEASUREMENT},device_id={data['device_id']} "
                    f"temperature={data['temperature']},humidity={data['humidity']},"
                    f"cpu_usage={data['cpu_usage']},mem_usage={data['mem_usage']} "
                    f"{data['timestamp']}"
                )
                batch_records.append(record)
            
            # 批量写入
            records_str = "\n".join(batch_records)
            client.write(record=records_str)
            total_records += len(batch_records)
            
            # 显示进度和告警
            progress = "█" * (second // 2)
            status = f"[{second:2d}/60] {progress:<30}"
            
            if batch_alerts:
                print(f"{status} 📊 {total_records} 条 | 🚨 {total_alerts} 次告警")
                for device, alerts in batch_alerts:
                    for alert in alerts:
                        print(f"         └─ {device}: {alert}")
            else:
                print(f"{status} 📊 {total_records} 条 | ✅ 正常")
            
            time.sleep(1)  # 每秒采集一次
    
    except KeyboardInterrupt:
        print("\n\n⚠️  监控已手动停止")
    
    # 统计报告
    print("\n" + "=" * 70)
    print("📊 监控报告")
    print("=" * 70)
    print(f"✅ 总采集数据: {total_records} 条")
    print(f"🚨 总告警次数: {total_alerts} 次")
    print(f"   ├─ 🔥 高温告警: {alert_stats['high_temp']} 次")
    print(f"   ├─ ⚠️  CPU告警: {alert_stats['high_cpu']} 次")
    print(f"   └─ 💧 湿度告警: {alert_stats['low_humidity']} 次")
    
    # 查询验证
    print("\n🔍 查询最近的异常数据...")
    try:
        result = client.query(f"""
            SELECT device_id, temperature, cpu_usage, humidity, time
            FROM {MEASUREMENT}
            WHERE temperature > {TEMP_HIGH} OR cpu_usage > {CPU_HIGH} OR humidity < {HUMIDITY_LOW}
            ORDER BY time DESC
            LIMIT 10
        """)
        print(f"\n最近 10 条异常记录：")
        print(result)
    except Exception as e:
        print(f"查询失败: {e}")
    
    print("\n✅ 监控完成！")
    print("=" * 70)

if __name__ == "__main__":
    main()
