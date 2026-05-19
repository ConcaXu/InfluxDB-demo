"""
实战场景 3：异常检测与根因分析
模拟真实的故障诊断场景：检测异常模式并分析原因

场景：
- 模拟 5 个服务器的运行数据
- 其中 1 台服务器会出现性能问题（CPU 和内存同时飙升）
- 使用统计方法检测异常（3-sigma 原则）
- 分析异常发生的时间段和关联指标
"""

import time
import random
import numpy as np
from datetime import datetime
from influxdb_client_3 import InfluxDBClient3

# 配置
HOST = "http://localhost:8181"
TOKEN = "apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ"
DATABASE = "concaxu"
MEASUREMENT = "server_metrics"

def generate_normal_data(server_id, timestamp):
    """生成正常的服务器指标"""
    return {
        "server_id": f"server_{server_id}",
        "cpu_usage": round(random.uniform(20, 50), 2),
        "mem_usage": round(random.uniform(30, 60), 2),
        "disk_io": round(random.uniform(100, 500), 2),
        "network_io": round(random.uniform(50, 200), 2),
        "response_time": round(random.uniform(50, 150), 2),
        "timestamp": timestamp
    }

def generate_anomaly_data(server_id, timestamp, severity):
    """生成异常的服务器指标（模拟故障）"""
    return {
        "server_id": f"server_{server_id}",
        "cpu_usage": round(random.uniform(80, 98), 2),  # CPU 飙升
        "mem_usage": round(random.uniform(85, 95), 2),  # 内存飙升
        "disk_io": round(random.uniform(800, 1500), 2),  # 磁盘 IO 增加
        "network_io": round(random.uniform(50, 200), 2),  # 网络正常
        "response_time": round(random.uniform(500, 2000), 2),  # 响应时间变长
        "timestamp": timestamp
    }

def write_simulation_data(client, duration_seconds=300):
    """写入模拟数据，其中 server_3 在中间时段出现异常"""
    print(f"📝 生成 {duration_seconds} 秒的模拟数据...")
    print(f"   server_3 将在 100-200 秒时出现异常\n")
    
    base_timestamp = int(time.time() * 1_000_000_000)
    total_records = 0
    anomaly_count = 0
    
    for second in range(duration_seconds):
        records = []
        
        for server_id in range(1, 6):  # 5 台服务器
            timestamp = base_timestamp + second * 1_000_000_000 + server_id * 100_000_000
            
            # server_3 在 100-200 秒时出现异常
            if server_id == 3 and 100 <= second < 200:
                data = generate_anomaly_data(server_id, timestamp, severity=(second - 100) / 100)
                anomaly_count += 1
            else:
                data = generate_normal_data(server_id, timestamp)
            
            record = (
                f"{MEASUREMENT},server_id={data['server_id']} "
                f"cpu_usage={data['cpu_usage']},mem_usage={data['mem_usage']},"
                f"disk_io={data['disk_io']},network_io={data['network_io']},"
                f"response_time={data['response_time']} {data['timestamp']}"
            )
            records.append(record)
        
        # 每 10 秒批量写入一次
        if (second + 1) % 10 == 0:
            records_str = "\n".join(records)
            client.write(record=records_str)
            total_records += len(records)
            print(f"  写入进度: {(second + 1) / duration_seconds * 100:5.1f}% ({total_records:,} 条)")
    
    print(f"\n✅ 数据写入完成: {total_records:,} 条（含 {anomaly_count} 条异常）\n")

def detect_anomalies(client):
    """使用统计方法检测异常"""
    print("🔍 检测异常数据（3-sigma 原则）...\n")
    
    # 查询所有数据
    query = f"""
        SELECT 
            server_id,
            cpu_usage,
            mem_usage,
            disk_io,
            response_time,
            time
        FROM {MEASUREMENT}
        ORDER BY time
    """
    
    result = client.query(query)
    df = result.to_pandas()
    
    print(f"📊 数据总量: {len(df)} 条\n")
    
    # 按服务器分组统计
    print("📈 各服务器统计信息:")
    print("-" * 90)
    print(f"{'服务器':<12} {'CPU均值':<10} {'CPU标准差':<12} {'内存均值':<10} {'响应时间均值':<12}")
    print("-" * 90)
    
    anomaly_servers = []
    
    for server in df['server_id'].unique():
        server_data = df[df['server_id'] == server]
        
        cpu_mean = server_data['cpu_usage'].mean()
        cpu_std = server_data['cpu_usage'].std()
        mem_mean = server_data['mem_usage'].mean()
        resp_mean = server_data['response_time'].mean()
        
        print(f"{server:<12} {cpu_mean:>8.2f}% {cpu_std:>10.2f}% {mem_mean:>8.2f}% {resp_mean:>10.2f}ms")
        
        # 检测异常：CPU 或内存均值超过 70%
        if cpu_mean > 70 or mem_mean > 70:
            anomaly_servers.append(server)
    
    print("-" * 90)
    print()
    
    if anomaly_servers:
        print(f"🚨 检测到异常服务器: {', '.join(anomaly_servers)}\n")
        
        # 详细分析异常服务器
        for server in anomaly_servers:
            print(f"🔬 分析 {server} 的异常模式:")
            
            query = f"""
                SELECT 
                    AVG(cpu_usage) as avg_cpu,
                    MAX(cpu_usage) as max_cpu,
                    AVG(mem_usage) as avg_mem,
                    MAX(mem_usage) as max_mem,
                    AVG(response_time) as avg_resp,
                    MAX(response_time) as max_resp,
                    COUNT(*) as count
                FROM {MEASUREMENT}
                WHERE server_id = '{server}'
            """
            
            result = client.query(query)
            stats = result.to_pandas().iloc[0]
            
            print(f"  CPU 使用率: 平均 {stats['avg_cpu']:.2f}%, 峰值 {stats['max_cpu']:.2f}%")
            print(f"  内存使用率: 平均 {stats['avg_mem']:.2f}%, 峰值 {stats['max_mem']:.2f}%")
            print(f"  响应时间: 平均 {stats['avg_resp']:.2f}ms, 峰值 {stats['max_resp']:.2f}ms")
            print(f"  数据点数: {int(stats['count'])} 条")
            print()
    else:
        print("✅ 未检测到异常服务器\n")

def correlation_analysis(client):
    """关联分析：查看指标之间的关系"""
    print("🔗 关联分析：CPU vs 响应时间\n")
    
    query = f"""
        SELECT 
            server_id,
            cpu_usage,
            response_time
        FROM {MEASUREMENT}
        WHERE cpu_usage > 80
        ORDER BY response_time DESC
        LIMIT 10
    """
    
    result = client.query(query)
    df = result.to_pandas()
    
    if len(df) > 0:
        print("高 CPU 使用率时的响应时间（Top 10）:")
        print(df.to_string(index=False))
        print()
        
        # 计算相关性
        print(f"📊 CPU 与响应时间的相关性分析:")
        print(f"  当 CPU > 80% 时，平均响应时间: {df['response_time'].mean():.2f}ms")
        print(f"  最大响应时间: {df['response_time'].max():.2f}ms")
        print()
    else:
        print("  未发现 CPU > 80% 的情况\n")

def main():
    print("=" * 70)
    print("🔍 实战场景 3：异常检测与根因分析")
    print("=" * 70)
    print(f"🖥️  服务器数量: 5 台")
    print(f"⏱️  监控时长: 300 秒（5 分钟）")
    print(f"🚨 异常场景: server_3 在 100-200 秒时出现性能问题")
    print("=" * 70)
    print()
    
    # 连接数据库
    client = InfluxDBClient3(host=HOST, token=TOKEN, database=DATABASE)
    
    print("🔌 连接 InfluxDB...")
    try:
        client.write(record=f"{MEASUREMENT},server_id=test cpu=25.0")
        print("✅ 连接成功！\n")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 步骤 1：写入模拟数据
    write_simulation_data(client, duration_seconds=300)
    
    # 步骤 2：异常检测
    detect_anomalies(client)
    
    # 步骤 3：关联分析
    correlation_analysis(client)
    
    # 步骤 4：时间序列分析
    print("📈 时间序列分析：查看 server_3 的指标变化\n")
    try:
        query = f"""
            SELECT 
                cpu_usage,
                mem_usage,
                response_time
            FROM {MEASUREMENT}
            WHERE server_id = 'server_3'
            ORDER BY time
            LIMIT 10
        """
        result = client.query(query)
        print("server_3 的前 10 条数据:")
        print(result)
        print()
    except Exception as e:
        print(f"  查询失败: {e}\n")
    
    print("=" * 70)
    print("✅ 异常检测完成！")
    print("=" * 70)
    print("\n💡 实战要点:")
    print("  1. 使用统计方法（均值、标准差）检测异常")
    print("  2. 对比正常和异常服务器的指标差异")
    print("  3. 分析多个指标的关联性（CPU vs 响应时间）")
    print("  4. 时序数据库可以快速定位异常时间段")
    print("  5. 实际生产中可以设置自动告警规则")

if __name__ == "__main__":
    main()
