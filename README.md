# 📘 InfluxDB 3 完全操作手册

> 类似 MySQL 的 CRUD 命令参考 + 高级操作 + 实战场景

> ⚠️ **重要提示**: InfluxDB 3 Core 只支持 **SELECT、SHOW、DESCRIBE** 查询操作，不支持 DELETE、UPDATE、INSERT 等修改操作！

---

## 📑 目录

- [快速开始](#快速开始)
- [基础 CRUD 操作](#基础-crud-操作)
- [高级查询操作](#高级查询操作)
- [数据管理](#数据管理)
- [性能优化](#性能优化)
- [实战场景](#实战场景)
- [常用命令速查](#常用命令速查)

---

## 🚀 快速开始

### 1. 连接数据库

```python
from influxdb_client_3 import InfluxDBClient3

# 创建客户端连接
client = InfluxDBClient3(
    host="http://localhost:8181",
    token="your_token_here",
    database="your_database"
)
```

### 2. 验证连接

```python
# 查看所有表（支持）
tables = client.query("SHOW TABLES")
print(tables)

# 查看数据库信息（不支持）
# databases = client.query("SHOW DATABASES")  # ❌ 不支持

# 测试基本查询
result = client.query("SELECT COUNT(*) FROM sensor_data")
print(f"数据总量: {result}")
```

---

## 📝 基础 CRUD 操作

### ✅ CREATE (写入数据)

#### 1. 单条数据写入

```python
# 基本格式：measurement,tag1=value1,tag2=value2 field1=value1,field2=value2 timestamp
client.write(
    record="sensor_data,device_id=device001,location=room1 temperature=25.6,humidity=62"
)
```

#### 2. 带时间戳写入

```python
import time

# 纳秒级时间戳
timestamp = int(time.time() * 1_000_000_000)
client.write(
    record=f"sensor_data,device_id=device001 temperature=25.6 {timestamp}"
)
```

#### 3. 批量写入（推荐）

```python
records = [
    "sensor_data,device_id=device001 temperature=25.6,humidity=62",
    "sensor_data,device_id=device002 temperature=26.3,humidity=58",
    "sensor_data,device_id=device003 temperature=24.8,humidity=65"
]

# 方法1：换行符分隔（推荐）
client.write(record="\n".join(records))

# 方法2：循环写入（不推荐，性能差）
for record in records:
    client.write(record=record)
```

#### 4. 批量生成数据

```python
import random

def generate_batch_data(count=1000):
    records = []
    base_ts = int(time.time() * 1_000_000_000)
    
    for i in range(count):
        device = f"device_{i % 10:03d}"
        temp = round(random.uniform(20.0, 35.0), 2)
        humidity = round(random.uniform(40.0, 80.0), 2)
        ts = base_ts + i * 1000  # 每条间隔1微秒
        
        record = f"sensor_data,device_id={device} temperature={temp},humidity={humidity} {ts}"
        records.append(record)
    
    return "\n".join(records)

# 写入1000条数据
client.write(record=generate_batch_data(1000))
```

---

### 🔍 READ (查询数据)

#### 1. 基础查询

```sql
-- 查询所有数据（危险！）
SELECT * FROM sensor_data

-- 限制返回数量
SELECT * FROM sensor_data LIMIT 10

-- 查询特定字段
SELECT device_id, temperature, humidity FROM sensor_data LIMIT 100
```

#### 2. 条件查询（WHERE）

```sql
-- 单条件
SELECT * FROM sensor_data WHERE device_id = 'device001'

-- 多条件（AND）
SELECT * FROM sensor_data 
WHERE device_id = 'device001' AND temperature > 25

-- 多条件（OR）
SELECT * FROM sensor_data 
WHERE temperature > 30 OR humidity < 40

-- 范围查询
SELECT * FROM sensor_data 
WHERE temperature BETWEEN 20 AND 30

-- IN 查询
SELECT * FROM sensor_data 
WHERE device_id IN ('device001', 'device002', 'device003')

-- LIKE 模糊查询
SELECT * FROM sensor_data 
WHERE device_id LIKE 'device_00%'
```

#### 3. 时间范围查询

```sql
-- 最近1小时
SELECT * FROM sensor_data 
WHERE time >= now() - INTERVAL '1 hour'

-- 最近24小时
SELECT * FROM sensor_data 
WHERE time >= now() - INTERVAL '1 day'

-- 指定时间范围
SELECT * FROM sensor_data 
WHERE time >= '2026-05-19T00:00:00Z' 
  AND time < '2026-05-19T23:59:59Z'

-- 最近N条记录
SELECT * FROM sensor_data 
ORDER BY time DESC 
LIMIT 100
```

#### 4. Python 查询示例

```python
# 基础查询
result = client.query("SELECT * FROM sensor_data LIMIT 10")
print(result)

# 参数化查询
device_id = "device001"
query = f"SELECT * FROM sensor_data WHERE device_id = '{device_id}' LIMIT 100"
result = client.query(query)

# 转换为 Pandas DataFrame
import pandas as pd
df = result.to_pandas()
print(df.head())
```

---

### ✏️ UPDATE (更新数据)

> ⚠️ **注意**: InfluxDB 是时序数据库，不支持传统的 UPDATE 操作！
> 
> 如果写入相同的 measurement + tags + timestamp，新数据会**覆盖**旧数据。

#### 覆盖式更新

```python
# 第一次写入
client.write("sensor_data,device_id=device001 temperature=25.0 1716076800000000000")

# 第二次写入（相同时间戳）→ 会覆盖
client.write("sensor_data,device_id=device001 temperature=26.5 1716076800000000000")

# 结果：只保留 temperature=26.5
```

---

### 🗑️ DELETE (删除数据)

> ❌ **重要**: InfluxDB 3 Core 版本**不支持** DELETE 操作！
> 
> 错误信息：`Query must start with SELECT, SHOW, or DESCRIBE`

#### ❌ 不支持的操作

```sql
-- ❌ 这些操作都会失败
DELETE FROM sensor_data
DELETE FROM sensor_data WHERE device_id = 'device001'
UPDATE sensor_data SET temperature = 30 WHERE device_id = 'device001'
INSERT INTO sensor_data VALUES (...)
DROP TABLE sensor_data
```

#### ✅ 替代方案

**1. 重建数据库（清空所有数据）**

```bash
# 使用 InfluxDB CLI（如果有）
influxdb3 database delete your_database
influxdb3 database create your_database
```

**2. 使用新的 Measurement 名称**

```python
# 不再使用旧表名，改用新名称
client.write("sensor_data_v2,device_id=device001 temperature=25.6")

# 查询时使用新表名
result = client.query("SELECT * FROM sensor_data_v2")
```

**3. 时间过滤查询（忽略旧数据）**

```python
# 只查询指定时间后的数据，忽略测试数据
query = """
SELECT * FROM sensor_data 
WHERE time >= '2026-05-19T14:00:00Z'  -- 只要今天下午2点后的数据
  AND device_id != 'test'  -- 排除测试设备
"""
result = client.query(query)
```

**4. 使用状态标记（软删除）**

```python
# 标记为已删除（而不是真正删除）
client.write('sensor_data,device_id=test001,status=deleted temperature=0')

# 查询时过滤掉已删除的数据
query = """
SELECT * FROM sensor_data 
WHERE status != 'deleted' OR status IS NULL
"""
```

**5. 测试环境隔离**

```python
# 生产环境
client_prod = InfluxDBClient3(database="production")

# 测试环境（可以随时重建）
client_test = InfluxDBClient3(database="test_db")
```

---

## 🎯 高级查询操作

### 1. 聚合函数

#### ✅ 支持的聚合函数

```sql
-- COUNT - 计数（支持）
SELECT COUNT(temperature) FROM sensor_data          -- ✅ 支持

-- 按设备计数
SELECT device_id, COUNT(*) as count 
FROM sensor_data 
GROUP BY device_id                                  -- ✅ 支持

-- AVG - 平均值（支持）
SELECT AVG(temperature) as avg_temp FROM sensor_data -- ✅ 支持

-- 按设备平均
SELECT device_id, AVG(temperature) as avg_temp 
FROM sensor_data 
GROUP BY device_id                                  -- ✅ 支持

-- MAX/MIN - 最大最小值（支持）
SELECT MAX(temperature) as max_temp FROM sensor_data -- ✅ 支持
SELECT MIN(temperature) as min_temp FROM sensor_data -- ✅ 支持

-- SUM - 求和（支持）
SELECT SUM(temperature) FROM sensor_data            -- ✅ 支持

-- STDDEV - 标准差（支持）
SELECT STDDEV(temperature) FROM sensor_data         -- ✅ 支持

-- 温度范围计算
SELECT 
    device_id,
    MIN(temperature) as min_temp,
    MAX(temperature) as max_temp,
    MAX(temperature) - MIN(temperature) as temp_range
FROM sensor_data 
GROUP BY device_id                                  -- ✅ 支持
```

### 2. 时间查询

#### ✅ 支持的时间操作

```sql
-- 查询时间字段
SELECT time FROM sensor_data LIMIT 10               -- ✅ 支持

-- 按时间排序
SELECT * FROM sensor_data ORDER BY time DESC LIMIT 10  -- ✅ 支持

-- 时间范围查询
SELECT * FROM sensor_data 
WHERE time >= now() - INTERVAL '1 hour'             -- ✅ 支持

-- 指定时间范围
SELECT * FROM sensor_data 
WHERE time >= '2026-05-19T00:00:00Z' 
  AND time < '2026-05-19T23:59:59Z'                 -- ✅ 支持
```

#### ❌ 不支持的时间函数

```sql
SELECT COUNT(*) FROM sensor_data                    -- ❌ 不支持
-- time_bucket 时间分桶（不支持）
SELECT time_bucket(INTERVAL '5 minutes', time) as bucket, AVG(temperature)
FROM sensor_data GROUP BY bucket                    -- ❌ 不支持

-- 替代方案：使用 DATE_TRUNC（需测试）
SELECT 
    DATE_TRUNC('hour', time) as hour,
    AVG(temperature) as avg_temp
FROM sensor_data 
GROUP BY hour
ORDER BY hour                                       -- 可能支持，需测试
```

### 3. 条件表达式

#### ✅ CASE WHEN（支持）

```sql
-- 温度等级分类
SELECT 
    device_id,
    temperature,
    CASE 
        WHEN temperature < 20 THEN '低温'
        WHEN temperature BETWEEN 20 AND 30 THEN '正常'
        WHEN temperature > 30 THEN '高温'
    END as temp_level
FROM sensor_data                                    -- ✅ 支持

-- 告警状态
SELECT 
    device_id,
    temperature,
    cpu_usage,
    CASE 
        WHEN temperature > 35 OR cpu_usage > 90 THEN 'CRITICAL'
        WHEN temperature > 30 OR cpu_usage > 80 THEN 'WARNING'
        ELSE 'NORMAL'
    END as alert_status
FROM sensor_data                                    -- ✅ 支持
```

-- 每小时聚合
SELECT 
    time_bucket(INTERVAL '1 hour', time) as hour,
    device_id,
    AVG(temperature) as avg_temp,
    MAX(temperature) as max_temp,
    MIN(temperature) as min_temp
FROM sensor_data 
GROUP BY hour, device_id
ORDER BY hour DESC
```

### 3. CASE WHEN 条件表达式

```sql
-- 温度等级分类
SELECT 
    device_id,
    temperature,
    CASE 
        WHEN temperature < 20 THEN '低温'
        WHEN temperature BETWEEN 20 AND 30 THEN '正常'
        WHEN temperature > 30 THEN '高温'
    END as temp_level
FROM sensor_data

-- 告警状态
SELECT 
    device_id,
    temperature,
    cpu_usage,
    CASE 
        WHEN temperature > 35 OR cpu_usage > 90 THEN 'CRITICAL'
        WHEN temperature > 30 OR cpu_usage > 80 THEN 'WARNING'
        ELSE 'NORMAL'
    END as alert_status
FROM sensor_data
```

---

## ⚡ 性能优化

### 1. 写入优化

#### ✅ 推荐做法

```python
# 1. 批量写入（每批 1000-5000 条）
BATCH_SIZE = 2000
records = generate_records(BATCH_SIZE)
client.write(record="\n".join(records))

# 2. 使用唯一时间戳
base_ts = int(time.time() * 1_000_000_000)
for i in range(count):
    ts = base_ts + i * 1000  # 每条间隔1微秒
```

#### ❌ 避免做法

```python
# 1. 逐条写入（慢100倍）
for record in records:
    client.write(record=record)  # ❌

# 2. 时间戳重复（数据会被覆盖）
for i in range(100):
    client.write("sensor_data,device_id=d1 temp=25.0")  # ❌
```

### 2. 查询优化

```sql
-- ✅ 使用标签过滤（走索引）
SELECT * FROM sensor_data WHERE device_id = 'device001'

-- ✅ 限制时间范围
SELECT * FROM sensor_data 
WHERE time >= now() - INTERVAL '1 hour'

-- ✅ 使用 LIMIT
SELECT * FROM sensor_data LIMIT 1000

-- ❌ 全表扫描
SELECT * FROM sensor_data  -- 数据量大时很慢
```

---

## 🎯 实战场景

### 场景1：实时监控告警

```python
def monitor_realtime(duration=60):
    """实时监控并告警"""
    start_time = time.time()
    alert_count = 0
    
    while time.time() - start_time < duration:
        query = """
        SELECT device_id, temperature, cpu_usage 
        FROM sensor_data 
        WHERE time >= now() - INTERVAL '10 seconds'
        """
        result = client.query(query)
        
        for row in result:
            if row['temperature'] > 30:
                print(f"🔥 高温告警: {row['device_id']} 温度 {row['temperature']}°C")
                alert_count += 1
            
            if row['cpu_usage'] > 80:
                print(f"⚠️ CPU告警: {row['device_id']} CPU {row['cpu_usage']}%")
                alert_count += 1
        
        time.sleep(5)
    
    print(f"\n监控完成，共触发 {alert_count} 次告警")
```

### 场景2：数据降采样

```python
def downsample_data():
    """将高频数据降采样为每小时统计"""
    query = """
    SELECT 
        time_bucket(INTERVAL '1 hour', time) as hour,
        device_id,
        AVG(temperature) as avg_temp,
        MAX(temperature) as max_temp,
        MIN(temperature) as min_temp,
        COUNT(*) as sample_count
    FROM sensor_data 
    WHERE time >= now() - INTERVAL '7 days'
    GROUP BY hour, device_id
    ORDER BY hour DESC
    """
    
    result = client.query(query)
    df = result.to_pandas()
    df.to_csv("downsampled_data.csv", index=False)
    print(f"降采样完成，生成 {len(df)} 条聚合数据")
```

### 场景3：异常检测

```python
def detect_anomalies():
    """使用 3-sigma 原则检测异常"""
    # 计算统计指标
    stats_query = """
    SELECT 
        device_id,
        AVG(temperature) as avg_temp,
        STDDEV(temperature) as std_temp
    FROM sensor_data 
    WHERE time >= now() - INTERVAL '1 hour'
    GROUP BY device_id
    """
    stats = client.query(stats_query).to_pandas()
    
    # 查询最近数据
    recent_query = """
    SELECT device_id, temperature, time
    FROM sensor_data 
    WHERE time >= now() - INTERVAL '5 minutes'
    """
    recent = client.query(recent_query).to_pandas()
    
    # 检测异常
    anomalies = []
    for _, row in recent.iterrows():
        device_stats = stats[stats['device_id'] == row['device_id']].iloc[0]
        temp_threshold = device_stats['avg_temp'] + 3 * device_stats['std_temp']
        
        if row['temperature'] > temp_threshold:
            anomalies.append({
                'device_id': row['device_id'],
                'value': row['temperature'],
                'threshold': temp_threshold
            })
    
    if anomalies:
        print(f"🚨 检测到 {len(anomalies)} 个异常")
        for a in anomalies:
            print(f"  - {a['device_id']}: {a['value']:.2f} (阈值: {a['threshold']:.2f})")
    else:
        print("✅ 未检测到异常")
```

---

## 📋 常用命令速查表

### InfluxDB 3 功能支持总结

#### ✅ 完全支持的操作

| 类别 | 操作 | 示例 |
|------|------|------|
| **基础查询** | SELECT | `SELECT * FROM sensor_data LIMIT 10` |
| | WHERE 条件 | `SELECT * FROM sensor_data WHERE device_id = 'device001'` |
| | ORDER BY | `SELECT * FROM sensor_data ORDER BY time DESC` |
| | LIMIT | `SELECT * FROM sensor_data LIMIT 100` |
| **聚合函数** | COUNT | `SELECT COUNT(*) FROM sensor_data` |
| | AVG | `SELECT AVG(temperature) FROM sensor_data` |
| | MAX/MIN | `SELECT MAX(temperature), MIN(temperature) FROM sensor_data` |
| | SUM | `SELECT SUM(temperature) FROM sensor_data` |
| | STDDEV | `SELECT STDDEV(temperature) FROM sensor_data` |
| **分组查询** | GROUP BY | `SELECT device_id, COUNT(*) FROM sensor_data GROUP BY device_id` |
| **条件表达式** | CASE WHEN | `SELECT CASE WHEN temperature > 30 THEN 'HIGH' ELSE 'NORMAL' END` |
| **时间查询** | 时间范围 | `SELECT * FROM sensor_data WHERE time >= now() - INTERVAL '1 hour'` |
| | 时间排序 | `SELECT * FROM sensor_data ORDER BY time DESC` |
| **元数据** | SHOW TABLES | `SHOW TABLES` |
| | DESCRIBE | `DESCRIBE sensor_data` |

#### ❌ 不支持的操作

| 类别 | 操作 | 错误信息 |
|------|------|----------|
| **数据修改** | DELETE | `Query must start with SELECT, SHOW, or DESCRIBE` |
| | UPDATE | `Query must start with SELECT, SHOW, or DESCRIBE` |
| | INSERT | `Query must start with SELECT, SHOW, or DESCRIBE` |
| **结构修改** | DROP TABLE | `Query must start with SELECT, SHOW, or DESCRIBE` |
| | CREATE TABLE | `Query must start with SELECT, SHOW, or DESCRIBE` |
| **元数据** | SHOW DATABASES | `Unsupported SQL statement: SHOW DATABASES` |
| **时间函数** | time_bucket | `Invalid function 'time_bucket'` |

#### ⚠️ 需要测试的操作

| 操作 | 说明 |
|------|------|
| DATE_TRUNC | 时间截断函数，可能支持 |
| 子查询 | 嵌套查询，需要测试 |
| 窗口函数 | OVER 子句，需要测试 |
| JOIN | 表连接，需要测试 |

### 数据库操作

| 操作 | SQL 命令 | 支持状态 |
|------|---------|---------|
| 查看表 | SHOW TABLES | ✅ 支持 |
| 查看表结构 | DESCRIBE table_name | ✅ 支持 |
| 查看数据库 | SHOW DATABASES | ❌ 不支持 |
| 删除数据 | DELETE FROM table | ❌ 不支持 |
| 更新数据 | UPDATE table SET ... | ❌ 不支持 |
| 插入数据 | INSERT INTO table ... | ❌ 不支持 |
| 删除表 | DROP TABLE table | ❌ 不支持 |

### 数据写入

| 操作 | Line Protocol |
|------|--------------|
| 单条写入 | measurement,tag=value field=value |
| 带时间戳 | measurement,tag=value field=value timestamp |
| 批量写入 | 多行用 \n 分隔 |

### 数据查询

| 操作 | SQL 命令 |
|------|---------|
| 查询全部 | SELECT * FROM table LIMIT 100 |
| 条件查询 | SELECT * FROM table WHERE tag='value' |
| 时间范围 | WHERE time >= now() - INTERVAL '1 hour' |
| 排序 | ORDER BY time DESC |

### 聚合函数

| 函数 | 示例 |
|------|------|
| COUNT | SELECT COUNT(*) FROM table |
| AVG | SELECT AVG(field) FROM table |
| MAX | SELECT MAX(field) FROM table |
| MIN | SELECT MIN(field) FROM table |
| SUM | SELECT SUM(field) FROM table |

---

## 🔧 常见问题

### Q1: 数据写入成功但查询不到？

**原因**: 时间戳相同导致数据被覆盖

**解决**:
```python
# 确保每条记录有唯一时间戳
base_ts = int(time.time() * 1_000_000_000)
for i in range(count):
    ts = base_ts + i * 1000
    record = f"sensor_data,device_id=d{i} temp=25.0 {ts}"
```

### Q2: 批量写入失败？

**原因**: 使用了列表而不是字符串

**解决**:
```python
# ✅ 正确
client.write(record="\n".join(records))

# ❌ 错误
client.write(record=records)
```

### Q3: SHOW DATABASES 失败？

**错误信息**: `Unsupported SQL statement: SHOW DATABASES`

**原因**: InfluxDB 3 Core 不支持 `SHOW DATABASES` 命令

**解决方案**:
```python
# ❌ 不支持
# client.query("SHOW DATABASES")

# ✅ 替代方案：通过连接配置知道数据库名
print(f"当前数据库: {client.database}")

# ✅ 或者查看表来确认连接
tables = client.query("SHOW TABLES")
print(f"当前数据库的表: {tables}")
```

### Q4: time_bucket 函数失败？

**错误信息**: `Invalid function 'time_bucket'`

**原因**: InfluxDB 3 不支持 `time_bucket` 时间分桶函数

**解决方案**:
```sql
-- ❌ 不支持
SELECT time_bucket(INTERVAL '5 minutes', time) as bucket, AVG(temperature)
FROM sensor_data GROUP BY bucket

-- ✅ 替代方案：使用 DATE_TRUNC（需测试）
SELECT DATE_TRUNC('hour', time) as hour, AVG(temperature)
FROM sensor_data GROUP BY hour

-- ✅ 或者在应用层处理时间分组
SELECT time, temperature FROM sensor_data 
WHERE time >= now() - INTERVAL '1 hour'
ORDER BY time
```

### Q5: DELETE 操作失败？

**错误信息**: `Query must start with SELECT, SHOW, or DESCRIBE`

**原因**: InfluxDB 3 Core 不支持 DELETE、UPDATE、INSERT 等操作

**解决方案**:
```python
# 方案1: 重建数据库
# influxdb3 database delete test_db
# influxdb3 database create test_db

# 方案2: 使用新表名
client.write("sensor_data_new,device_id=device001 temperature=25.6")

# 方案3: 时间过滤查询
query = "SELECT * FROM sensor_data WHERE time >= '2026-05-19T14:00:00Z'"
```

### Q6: 查询很慢？

**原因**: 没有使用索引或时间范围

**解决**:
```sql
-- ✅ 使用 tag 过滤 + 时间范围
SELECT * FROM sensor_data 
WHERE device_id = 'device001' 
  AND time >= now() - INTERVAL '1 hour'
LIMIT 1000
```

### Q7: 如何清理测试数据？

**推荐做法**:
```python
# 1. 使用独立的测试数据库
client_test = InfluxDBClient3(database="test_db")

# 2. 使用测试专用的表名
client.write("test_sensor_data,device_id=test001 temperature=25.0")

# 3. 添加测试标记
client.write("sensor_data,device_id=device001,env=test temperature=25.0")

# 查询时排除测试数据
query = "SELECT * FROM sensor_data WHERE env != 'test' OR env IS NULL"
```

---

## 📚 学习资源

- [InfluxDB 3 官方文档](https://docs.influxdata.com/influxdb/v3/)
- [Line Protocol 语法](https://docs.influxdata.com/influxdb/v3/reference/syntax/line-protocol/)
- [SQL 查询参考](https://docs.influxdata.com/influxdb/v3/query-data/sql/)

---

**🎉 完成！现在你已经掌握了 InfluxDB 3 的核心操作！**

#### 4. 使用字典写入

```python
from influxdb_client_3 import Point

# 使用 Point 对象
point = Point("sensor_data") \
    .tag("device_id", "device001") \
    .tag("location", "room1") \
    .field("temperature", 25.6) \
    .field("humidity", 62.0)

client.write(record=point)
```

#### 5. 批量生成数据

```python
import random

def generate_batch_data(count=1000):
    records = []
    base_ts = int(time.time() * 1_000_000_000)
    
    for i in range(count):
        device = f"device_{i % 10:03d}"
        temp = round(random.uniform(20.0, 35.0), 2)
        humidity = round(random.uniform(40.0, 80.0), 2)
        ts = base_ts + i * 1000  # 每条间隔1微秒
        
        record = f"sensor_data,device_id={device} temperature={temp},humidity={humidity} {ts}"
        records.append(record)
    
    return "\n".join(records)

# 写入1000条数据
client.write(record=generate_batch_data(1000))
```

---

### 🔍 READ (查询数据)

#### 1. 基础查询

```sql
-- 查询所有数据（危险！）
SELECT * FROM sensor_data

-- 限制返回数量
SELECT * FROM sensor_data LIMIT 10

-- 查询特定字段
SELECT device_id, temperature, humidity FROM sensor_data LIMIT 100
```

#### 2. 条件查询（WHERE）

```sql
-- 单条件
SELECT * FROM sensor_data WHERE device_id = 'device001'

-- 多条件（AND）
SELECT * FROM sensor_data 
WHERE device_id = 'device001' AND temperature > 25

-- 多条件（OR）
SELECT * FROM sensor_data 
WHERE temperature > 30 OR humidity < 40

-- 范围查询
SELECT * FROM sensor_data 
WHERE temperature BETWEEN 20 AND 30

-- IN 查询
SELECT * FROM sensor_data 
WHERE device_id IN ('device001', 'device002', 'device003')

-- LIKE 模糊查询
SELECT * FROM sensor_data 
WHERE device_id LIKE 'device_00%'
```

#### 3. 时间范围查询

```sql
-- 最近1小时
SELECT * FROM sensor_data 
WHERE time >= now() - INTERVAL '1 hour'

-- 最近24小时
SELECT * FROM sensor_data 
WHERE time >= now() - INTERVAL '1 day'

-- 指定时间范围
SELECT * FROM sensor_data 
WHERE time >= '2026-05-19T00:00:00Z' 
  AND time < '2026-05-19T23:59:59Z'

-- 最近N条记录
SELECT * FROM sensor_data 
ORDER BY time DESC 
LIMIT 100
```

#### 4. 排序查询（ORDER BY）

```sql
-- 按时间升序
SELECT * FROM sensor_data ORDER BY time ASC LIMIT 10

-- 按时间降序（最新数据）
SELECT * FROM sensor_data ORDER BY time DESC LIMIT 10

-- 多字段排序
SELECT * FROM sensor_data 
ORDER BY device_id ASC, time DESC 
LIMIT 100
```

#### 5. Python 查询示例

```python
# 基础查询
result = client.query("SELECT * FROM sensor_data LIMIT 10")
print(result)

# 参数化查询（防止SQL注入）
device_id = "device001"
query = f"SELECT * FROM sensor_data WHERE device_id = '{device_id}' LIMIT 100"
result = client.query(query)

# 转换为 Pandas DataFrame
import pandas as pd
df = result.to_pandas()
print(df.head())

# 遍历结果
for row in result:
    print(f"Device: {row['device_id']}, Temp: {row['temperature']}")
```

---

### ✏️ UPDATE (更新数据)

> ⚠️ **注意**: InfluxDB 是时序数据库，不支持传统的 UPDATE 操作！
> 
> 如果写入相同的 measurement + tags + timestamp，新数据会**覆盖**旧数据。

#### 覆盖式更新

```python
# 第一次写入
client.write("sensor_data,device_id=device001 temperature=25.0 1716076800000000000")

# 第二次写入（相同时间戳）→ 会覆盖
client.write("sensor_data,device_id=device001 temperature=26.5 1716076800000000000")

# 结果：只保留 temperature=26.5
```

#### 追加新字段

```python
# 原始数据
client.write("sensor_data,device_id=device001 temperature=25.0")

# 追加新字段（不同时间戳）
client.write("sensor_data,device_id=device001 temperature=25.0,humidity=60")

# 结果：两条独立记录
```

---

### 🗑️ DELETE (删除数据)

> ⚠️ **注意**: InfluxDB 3 Core 版本可能不支持 DELETE！

#### 1. 删除整个 Measurement

```sql
-- 删除表（如果支持）
DELETE FROM sensor_data
```

#### 2. 条件删除

```sql
-- 删除特定设备数据
DELETE FROM sensor_data WHERE device_id = 'device001'

-- 删除时间范围数据
DELETE FROM sensor_data 
WHERE time < now() - INTERVAL '30 days'
```

#### 3. Python 删除示例

```python
try:
    client.query("DELETE FROM sensor_data WHERE device_id = 'device001'")
    print("删除成功")
except Exception as e:
    print(f"删除失败（可能不支持）: {e}")
```

#### 4. 替代方案：重建数据库

```bash
# 如果不支持 DELETE，可以重建数据库
influxdb3 database delete concaxu
influxdb3 database create concaxu
```

---

## 🎯 高级查询操作

### 1. 聚合函数

#### COUNT - 计数

```sql
-- 总记录数
SELECT COUNT(*) FROM sensor_data

-- 按设备计数
SELECT device_id, COUNT(*) as count 
FROM sensor_data 
GROUP BY device_id

-- 统计非空值
SELECT COUNT(temperature) FROM sensor_data
```

#### AVG - 平均值

```sql
-- 全局平均温度
SELECT AVG(temperature) as avg_temp FROM sensor_data

-- 按设备平均
SELECT device_id, AVG(temperature) as avg_temp 
FROM sensor_data 
GROUP BY device_id

-- 多字段平均
SELECT 
    device_id,
    AVG(temperature) as avg_temp,
    AVG(humidity) as avg_humidity
FROM sensor_data 
GROUP BY device_id
```

#### MAX / MIN - 最大最小值

```sql
-- 最高温度
SELECT MAX(temperature) as max_temp FROM sensor_data

-- 最低温度
SELECT MIN(temperature) as min_temp FROM sensor_data

-- 温度范围
SELECT 
    device_id,
    MIN(temperature) as min_temp,
    MAX(temperature) as max_temp,
    MAX(temperature) - MIN(temperature) as temp_range
FROM sensor_data 
GROUP BY device_id
```

#### SUM - 求和

```sql
-- 总CPU使用时间
SELECT SUM(cpu_usage) as total_cpu FROM sensor_data

-- 按设备求和
SELECT device_id, SUM(cpu_usage) as total_cpu 
FROM sensor_data 
GROUP BY device_id
```

---

### 2. 分组查询（GROUP BY）

#### 按标签分组

```sql
-- 按设备分组
SELECT device_id, COUNT(*) as count 
FROM sensor_data 
GROUP BY device_id

-- 按多个标签分组
SELECT device_id, location, AVG(temperature) as avg_temp 
FROM sensor_data 
GROUP BY device_id, location
```

#### 按时间窗口分组

```sql
-- 每5分钟聚合
SELECT 
    time_bucket(INTERVAL '5 minutes', time) as bucket,
    AVG(temperature) as avg_temp
FROM sensor_data 
GROUP BY bucket
ORDER BY bucket

-- 每小时聚合
SELECT 
    time_bucket(INTERVAL '1 hour', time) as hour,
    device_id,
    AVG(temperature) as avg_temp,
    MAX(temperature) as max_temp,
    MIN(temperature) as min_temp
FROM sensor_data 
GROUP BY hour, device_id
ORDER BY hour DESC

-- 每天聚合
SELECT 
    DATE_TRUNC('day', time) as day,
    COUNT(*) as count,
    AVG(temperature) as avg_temp
FROM sensor_data 
GROUP BY day
ORDER BY day
```
