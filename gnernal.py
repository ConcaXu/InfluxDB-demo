"""
InfluxDB 3 批量写入 10 万条性能测试 + 验证
模拟场景：10 个设备，每个设备上报温度 + 湿度 + CPU + 内存，共 10 万条

运行方式：
  python influxdb3_benchmark.py

前提：
  1. InfluxDB 3 Core 已在 localhost:8181 启动
  2. 已 pip install influxdb-client-3
  3. 已创建数据库 concaxu（或改成你自己的库名）
"""

import time
import random
import os
from influxdb_client_3 import InfluxDBClient3

# ==================== 配置区 ====================
HOST = "http://localhost:8181"
PORT = 8181
DATABASE = "concaxu"
TOKEN = "apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ"

# 测试参数
DEVICE_COUNT = 10            # 设备数量
TOTAL_RECORDS = 100_000      # 总写入条数
BATCH_SIZE = 2000            # 每批写入条数（可调大提速）
MEASUREMENT = "sensor_data"

# 关闭代理影响
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""


def generate_records(batch_size: int, start_idx: int) -> list[str]:
    """生成一批模拟数据（Line Protocol 格式）"""
    records = []
    locations = ["room_1", "room_2", "room_3", "room_4", "room_5"]
    
    # 获取当前时间戳（纳秒）
    base_timestamp = int(time.time() * 1_000_000_000)

    for i in range(batch_size):
        device_num = (start_idx + i) % DEVICE_COUNT
        device = f"device_{device_num:04d}"
        location = locations[device_num % len(locations)]

        temperature = round(random.uniform(20.0, 35.0), 2)
        humidity = round(random.uniform(40.0, 80.0), 2)
        cpu_usage = round(random.uniform(10.0, 95.0), 2)
        mem_usage = round(random.uniform(30.0, 90.0), 2)

        # 为每条记录生成唯一时间戳（递增纳秒）
        timestamp = base_timestamp + (start_idx + i) * 1000

        # Line Protocol: measurement,tag1=value1,tag2=value2 field1=value1,field2=value2 timestamp
        record = (
            f"{MEASUREMENT},device_id={device},location={location} "
            f"temperature={temperature},humidity={humidity},"
            f"cpu_usage={cpu_usage},mem_usage={mem_usage} {timestamp}"
        )
        records.append(record)

    return records


def print_banner():
    print("=" * 62)
    print("   🚀  InfluxDB 3 批量写入性能测试  🚀")
    print("=" * 62)
    print(f"  📊  目标数据量 ：{TOTAL_RECORDS:,} 条")
    print(f"  📦  每批写入   ：{BATCH_SIZE:,} 条")
    print(f"  🏷️   设备数量   ：{DEVICE_COUNT} 个")
    print(f"  📂  数据库     ：{DATABASE}")
    print(f"  📡  地址       ：{HOST}:{PORT}")
    print("=" * 62)


def main():
    print_banner()

    # 创建客户端
    client = InfluxDBClient3(
        host="http://localhost:8181",
        token="apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ",
        database="concaxu"
    )

    # 预热：先写一条测试数据，验证连接
    print("\n🔌 正在连接 InfluxDB...")
    try:
        client.write(record="sensor_data,device_id=test temperature=25.0")
        print("✅ 连接成功！")
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        print("   请确认：")
        print("   1. InfluxDB 3 是否在 localhost:8181 运行")
        print("   2. Token 是否正确")
        print("   3. 是否已创建数据库 concaxu")
        return

    # 清理旧数据
    print("\n🧹 清理旧测试数据...")
    try:
        client.query(f'DELETE FROM {MEASUREMENT}')
        print("✅ 旧数据已清理")
    except Exception as e:
        print(f"⚠️  清理失败（可能不支持 DELETE 或无旧数据）：{e}")
        print("   继续执行测试...")

    print("\n🚀 开始性能测试...\n")

    total_batches = (TOTAL_RECORDS + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📦 共分 {total_batches} 批写入\n")

    # ==================== 开始写入 ====================
    start_time = time.time()
    total_written = 0
    batch_times = []

    for batch_idx in range(total_batches):
        batch_start = time.time()

        remaining = TOTAL_RECORDS - total_written
        current_batch_size = min(BATCH_SIZE, remaining)

        records = generate_records(current_batch_size, total_written)
        
        # 调试：打印第一批的前 3 条数据
        if batch_idx == 0:
            print("📝 第一批数据示例（前3条）：")
            for idx, rec in enumerate(records[:3]):
                print(f"   {idx+1}. {rec}")
            print()
        
        try:
            # 方法1：将列表转换为换行符分隔的字符串
            records_str = "\n".join(records)
            client.write(record=records_str)
            total_written += current_batch_size
        except Exception as e:
            print(f"\n❌ 第 {batch_idx + 1} 批写入失败：{e}")
            print(f"   失败的记录示例：{records[0] if records else 'None'}")
            break

        batch_time = time.time() - batch_start
        batch_times.append(batch_time)

        avg_speed = current_batch_size / batch_time if batch_time > 0 else 0
        progress = total_written / TOTAL_RECORDS * 100
        elapsed = time.time() - start_time
        overall_speed = total_written / elapsed if elapsed > 0 else 0

        bar = "█" * int(progress / 2)
        print(
            f"  {bar:<50} {progress:5.1f}% | "
            f"第 {batch_idx + 1}/{total_batches} 批 | "
            f"{current_batch_size:,} 条 | "
            f"{avg_speed:>7,.0f} 条/s | "
            f"累计 {total_written:,}/{TOTAL_RECORDS:,}"
        )

    # ==================== 写入完成 ====================
    total_time = time.time() - start_time
    final_speed = total_written / total_time if total_time > 0 else 0
    min_batch = min(batch_times)
    max_batch = max(batch_times)
    avg_batch = sum(batch_times) / len(batch_times)

    print("\n" + "=" * 62)
    print("   🎉  写入完成！")
    print("=" * 62)
    print(f"  📊  总写入     ：{total_written:,} 条")
    print(f"  ⏱️   总耗时     ：{total_time:.2f} 秒")
    print(f"  🚀  平均速度   ：{final_speed:,.0f} 条/秒")
    print(f"  ⚡  最快一批   ：{min_batch:.2f}s ({BATCH_SIZE/min_batch:,.0f} 条/s)")
    print(f"  🐢  最慢一批   ：{max_batch:.2f}s ({BATCH_SIZE/max_batch:,.0f} 条/s)")
    print(f"  📊  平均每批   ：{avg_batch:.2f}s")
    print("=" * 62)

    # ==================== 验证数据 ====================
    print("\n🔍 验证写入结果...")

    try:
        result = client.query(
            f'SELECT COUNT(*) FROM {MEASUREMENT}'
        )
        print(f"  ✅ 数据总量：\n{result}")
    except Exception as e:
        print(f"  ⚠️ 验证查询失败：{e}")

    try:
        result = client.query(
            f'SELECT device_id, COUNT(*) as cnt FROM {MEASUREMENT} '
            f'GROUP BY device_id ORDER BY cnt DESC'
        )
        print(f"\n  📊 各设备数据量排行：\n{result}")
    except Exception as e:
        print(f"  ⚠️ 分组查询失败：{e}")

    try:
        result = client.query(
            f'SELECT device_id, AVG(temperature) as avg_temp, '
            f'AVG(humidity) as avg_humidity, AVG(cpu_usage) as avg_cpu, '
            f'AVG(mem_usage) as avg_mem FROM {MEASUREMENT} '
            f'GROUP BY device_id ORDER BY device_id'
        )
        print(f"\n  📈 各设备平均值：\n{result}")
    except Exception as e:
        print(f"  ⚠️ 聚合查询失败：{e}")

    print("\n✅ 全部完成！打开 Grafana 即可画图 🎉")


if __name__ == "__main__":
    main()