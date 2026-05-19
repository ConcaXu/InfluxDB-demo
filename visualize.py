"""
InfluxDB 3 数据可视化
从 sensor_data 表读取数据并绘制图表
"""

import matplotlib.pyplot as plt
import pandas as pd
from influxdb_client_3 import InfluxDBClient3
import matplotlib
matplotlib.use('TkAgg')  # 使用 TkAgg 后端

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 连接 InfluxDB
client = InfluxDBClient3(
    host="http://localhost:8181",
    token="apiv3_XXpf5IiY_IBzET2QJIpTiE1z-6NrgpNOnaoTtdMq7wJ9CO_FfiEKFhNY5Azi95ZvX890T-PU6JbzCXEAQfu4yQ",
    database="concaxu"
)

print("📊 正在从 InfluxDB 读取数据...")

# 查询数据
query = """
SELECT 
    device_id,
    time,
    temperature,
    humidity,
    cpu_usage,
    mem_usage
FROM sensor_data
ORDER BY time
LIMIT 10000
"""

result = client.query(query)
df = result.to_pandas()

print(f"✅ 读取了 {len(df)} 条数据")
print(f"📅 时间范围: {df['time'].min()} 到 {df['time'].max()}")
print(f"🏷️  设备列表: {df['device_id'].unique()}")

# 创建图表
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle('InfluxDB 传感器数据可视化', fontsize=16, fontweight='bold')

# 1. 温度趋势图（按设备）
ax1 = axes[0, 0]
for device in df['device_id'].unique()[:5]:  # 只显示前5个设备
    device_data = df[df['device_id'] == device]
    ax1.plot(device_data.index, device_data['temperature'], label=device, alpha=0.7)
ax1.set_title('温度趋势 (前5个设备)', fontsize=12, fontweight='bold')
ax1.set_xlabel('数据点索引')
ax1.set_ylabel('温度 (°C)')
ax1.legend(loc='best', fontsize=8)
ax1.grid(True, alpha=0.3)

# 2. 湿度趋势图（按设备）
ax2 = axes[0, 1]
for device in df['device_id'].unique()[:5]:
    device_data = df[df['device_id'] == device]
    ax2.plot(device_data.index, device_data['humidity'], label=device, alpha=0.7)
ax2.set_title('湿度趋势 (前5个设备)', fontsize=12, fontweight='bold')
ax2.set_xlabel('数据点索引')
ax2.set_ylabel('湿度 (%)')
ax2.legend(loc='best', fontsize=8)
ax2.grid(True, alpha=0.3)

# 3. CPU 使用率分布（箱线图）
ax3 = axes[1, 0]
cpu_data = [df[df['device_id'] == device]['cpu_usage'].values 
            for device in df['device_id'].unique()[:10]]
bp = ax3.boxplot(cpu_data, labels=[d.replace('device_', '') for d in df['device_id'].unique()[:10]], 
                 patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightblue')
ax3.set_title('CPU 使用率分布 (各设备)', fontsize=12, fontweight='bold')
ax3.set_xlabel('设备编号')
ax3.set_ylabel('CPU 使用率 (%)')
ax3.grid(True, alpha=0.3, axis='y')
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# 4. 内存使用率分布（箱线图）
ax4 = axes[1, 1]
mem_data = [df[df['device_id'] == device]['mem_usage'].values 
            for device in df['device_id'].unique()[:10]]
bp = ax4.boxplot(mem_data, labels=[d.replace('device_', '') for d in df['device_id'].unique()[:10]], 
                 patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightgreen')
ax4.set_title('内存使用率分布 (各设备)', fontsize=12, fontweight='bold')
ax4.set_xlabel('设备编号')
ax4.set_ylabel('内存使用率 (%)')
ax4.grid(True, alpha=0.3, axis='y')
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
plt.savefig('sensor_data_visualization.png', dpi=150, bbox_inches='tight')
print("\n✅ 图表已保存为 sensor_data_visualization.png")
plt.show()

# 打印统计信息
print("\n" + "="*60)
print("📊 数据统计摘要")
print("="*60)
print(f"\n各设备数据量:")
print(df['device_id'].value_counts().head(10))

print(f"\n温度统计:")
print(f"  平均值: {df['temperature'].mean():.2f}°C")
print(f"  最小值: {df['temperature'].min():.2f}°C")
print(f"  最大值: {df['temperature'].max():.2f}°C")

print(f"\n湿度统计:")
print(f"  平均值: {df['humidity'].mean():.2f}%")
print(f"  最小值: {df['humidity'].min():.2f}%")
print(f"  最大值: {df['humidity'].max():.2f}%")

print(f"\nCPU 使用率统计:")
print(f"  平均值: {df['cpu_usage'].mean():.2f}%")
print(f"  最小值: {df['cpu_usage'].min():.2f}%")
print(f"  最大值: {df['cpu_usage'].max():.2f}%")

print(f"\n内存使用率统计:")
print(f"  平均值: {df['mem_usage'].mean():.2f}%")
print(f"  最小值: {df['mem_usage'].min():.2f}%")
print(f"  最大值: {df['mem_usage'].max():.2f}%")
print("="*60)
