# InfluxDB 3 实战指南

## 📚 实战场景列表

### 🚨 实战 1：实时监控告警系统
**文件**: `实战1_实时监控告警.py`

**场景描述**:
- 模拟 10 个 IoT 传感器设备实时上报数据
- 每秒采集一次，持续监控 60 秒
- 实时检测异常并触发告警

**告警规则**:
- 🔥 温度 > 30°C → 高温告警
- ⚠️ CPU > 80% → 性能告警
- 💧 湿度 < 45% → 干燥告警

**运行方式**:
```bash
python 实战1_实时监控告警.py
```

**学习要点**:
- 实时数据写入
- 条件判断和告警逻辑
- 异常数据查询
- 统计报告生成

---

### 📊 实战 2：数据降采样与聚合分析
**文件**: `实战2_数据降采样聚合.py`

**场景描述**:
- 生成 1 小时的高频数据（36,000 条）
- 模拟真实的数据分析场景
- 按不同时间窗口聚合统计

**数据特点**:
- 温度缓慢上升趋势
- CPU 周期性波动
- 10 个设备并发采集

**运行方式**:
```bash
python 实战2_数据降采样聚合.py
```

**学习要点**:
- 大批量数据写入优化
- 时间窗口聚合查询
- AVG/MAX/MIN/COUNT 等聚合函数
- 查询性能对比
- 数据降采样策略

---

### 🔍 实战 3：异常检测与根因分析
**文件**: `实战3_异常检测分析.py`

**场景描述**:
- 模拟 5 台服务器的运行监控
- server_3 在 100-200 秒时出现性能故障
- 使用统计方法自动检测异常
- 分析故障根因和关联指标

**异常模式**:
- CPU 使用率飙升至 80-98%
- 内存使用率飙升至 85-95%
- 响应时间增加到 500-2000ms
- 磁盘 IO 显著增加

**运行方式**:
```bash
python 实战3_异常检测分析.py
```

**学习要点**:
- 3-sigma 异常检测原则
- 统计分析（均值、标准差）
- 多指标关联分析
- 时间序列模式识别
- 故障根因定位

---

## 🎯 实战学习路径

### 初级（第 1 天）
1. 运行 `实战1_实时监控告警.py`
2. 理解实时数据写入流程
3. 学习告警规则设置
4. 修改阈值，观察告警变化

### 中级（第 2-3 天）
1. 运行 `实战2_数据降采样聚合.py`
2. 理解批量写入优化
3. 学习聚合查询语法
4. 尝试不同的聚合窗口

### 高级（第 4-5 天）
1. 运行 `实战3_异常检测分析.py`
2. 理解异常检测算法
3. 学习多指标关联分析
4. 实现自定义检测规则

---

## 💡 实战技巧

### 1. 数据写入优化
```python
# ❌ 不推荐：逐条写入
for record in records:
    client.write(record=record)

# ✅ 推荐：批量写入
records_str = "\n".join(records)
client.write(record=records_str)
```

### 2. 时间戳处理
```python
# 使用纳秒级时间戳
timestamp = int(time.time() * 1_000_000_000)

# 确保每条记录时间戳唯一
for i in range(batch_size):
    ts = base_timestamp + i * 1000  # 每条间隔 1 微秒
```

### 3. Line Protocol 格式
```
measurement,tag1=value1,tag2=value2 field1=value1,field2=value2 timestamp
```

**注意**:
- tags 和 fields 之间有空格
- fields 之间用逗号分隔
- timestamp 是可选的（纳秒）

### 4. 查询优化
```sql
-- ✅ 使用索引（tags）
SELECT * FROM sensor_data WHERE device_id = 'device_001'

-- ✅ 限制返回数量
SELECT * FROM sensor_data LIMIT 1000

-- ✅ 使用聚合减少数据量
SELECT device_id, AVG(temperature) FROM sensor_data GROUP BY device_id
```

---

## 🔧 常见问题

### Q1: 数据写入成功但查询只有几条？
**A**: 可能是时间戳相同导致数据被覆盖。确保每条记录有唯一的时间戳。

### Q2: 批量写入失败？
**A**: 使用 `"\n".join(records)` 而不是 `records=list`，InfluxDB 3 的 Python 客户端对列表支持有限。

### Q3: 查询报错 "No field named time"？
**A**: 在聚合查询中，time 字段不会自动包含。如需时间，使用 `MIN(time)` 或 `MAX(time)`。

### Q4: 如何删除测试数据？
**A**: InfluxDB 3 Core 可能不支持 DELETE。建议重新创建数据库或使用时间过滤查询。

---

## 📈 进阶挑战

完成基础实战后，尝试这些挑战：

1. **实时仪表盘**: 结合 `visualize.py` 实时刷新图表
2. **多级告警**: 实现 WARNING/ERROR/CRITICAL 三级告警
3. **预测分析**: 基于历史数据预测未来趋势
4. **分布式监控**: 模拟多地域、多机房的监控场景
5. **性能压测**: 测试 InfluxDB 的写入和查询极限

---

## 🎓 学习资源

- [InfluxDB 3 官方文档](https://docs.influxdata.com/influxdb/v3/)
- [Line Protocol 语法](https://docs.influxdata.com/influxdb/v3/reference/syntax/line-protocol/)
- [SQL 查询参考](https://docs.influxdata.com/influxdb/v3/query-data/sql/)

---

## ✅ 实战检查清单

- [ ] 成功运行实战 1，看到告警信息
- [ ] 成功运行实战 2，完成 36,000 条数据写入
- [ ] 成功运行实战 3，检测到 server_3 异常
- [ ] 理解 Line Protocol 格式
- [ ] 掌握批量写入技巧
- [ ] 会写基本的聚合查询
- [ ] 能够分析异常数据
- [ ] 尝试修改代码实现自定义需求

---

**祝你实战顺利！🚀**
