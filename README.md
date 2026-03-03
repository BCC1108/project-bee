# Project BEE - 超轻量web3量化项目

一个基于Python的加密货币量化交易系统，提供策略回测、参数优化和实时交易功能。

## 核心功能

- **多策略支持**: BBands、MACD、BBI等技术指标策略
- **高效回测**: 基于VectorBT的高性能回测引擎，也集成了Backtrader做事件驱动回测
- **参数优化**: 多核并行参数扫描，实时内存释放机制(基于joblib)
- **实时交易**: 支持实时市场数据和交易执行
- **数据管理**: 使用Parquet格式存储，快速读写，输入输出缓存统一存放于database文件夹
- **可视化**: 交互式回测结果图表

## 快速开始

### 1. 环境配置
```bash
git clone https://github.com/BCC1108/project-bee.git
cd project-bee
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 配置环境
```bash
cp livetrade/.env.example livetrade/.env
# 编辑livetrade/.env，添加API密钥
```

### 3. 运行回测
```bash
python mainEntry/run.py
# 或运行示例策略
python examples/hq3BT.py
```

## 项目结构

<details>
<summary>点击查看项目结构</summary>

```
project-bee/
├── core/
│   ├── __init__.py
│   ├── strategyBook.py
│   ├── commonFunctions.py
│   └── plotFunction.py
├── database/
├── examples/
├── livetrade/
├── mainEntry/
└── simplescripts/
```

</details>

<details>
<summary>点击展开完整项目结构</summary>

```
project-bee/
├── core/                      # 核心模块
│   ├── __init__.py            # 模块导出
│   ├── strategyBook.py        # 策略库定义
│   ├── commonFunctions.py     # 通用工具函数
│   └── plotFunction.py        # 绘图功能
├── database/                  # 数据存储目录
│   ├── jlmemory/              # 内存缓存
│   ├── plotdatas/             # 绘图数据
│   ├── pressuretestLogs/      # 压力测试日志
│   ├── rowdatas/              # 原始数据
│   └── scanerOutputs/         # 扫描输出
├── examples/                  # 示例脚本集合
│   ├── hq3BT.py               # HQ3策略回测示例
│   ├── hq3simuRun.py          # HQ3模拟运行
│   ├── get_kline_data.py      # K线数据获取
│   └── ...                    # 其他示例脚本
├── livetrade/                 # 实时交易模块
│   ├── config.py              # 配置管理
│   ├── liveRun.py             # 实时交易运行
│   ├── .env_example           # 环境变量模板
│   └── .env                   # 环境变量（本地）
├── mainEntry/                 # 主运行入口
│   └── run.py                 # 主回测脚本
└── simplescripts/             # 简单脚本集合
    ├── btBT.py                # Backtrader回测
    ├── btVBT.py               # VectorBT回测
    ├── pressureTest.py        # 压力测试
    └── supaKline.py           # K线数据获取
```

</details>

## 内置策略
- **HQ2**: 基于BBands指标的基础策略
- **HQ3**: 改进的BBands策略（成交量确认）
- **HQ3.5**: HQ3变种，矩形平仓逻辑
- **HQ4**: 基于MACD指标的新策略
- **HQ5**: BBI快慢线策略

## 配置示例
```python
# mainEntry/run.py中配置
teststrat = Strategy(name='hq3.5', description='hq3变种, 矩形平仓', 
                     params={'window':20, 'stddev':2, 'bandwidthmax':0.2, 'bandwidthmin':0.05})
teststrat.original_freq = '1min'
teststrat.tPrate = 0.03  # 止盈比例
teststrat.sLrate = 0.08  # 止损比例
```

## 注意事项
1. 数据格式：项目默认使用Parquet格式
2. 内存使用：大规模参数扫描可能消耗大量内存
3. 实时交易：实盘前请充分测试，注意风险管理
4. API限制：注意交易所API调用频率限制

## 许可证
MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

**免责声明**: 本项目仅供学习和研究使用，不构成投资建议。加密货币交易存在高风险，请谨慎决策。