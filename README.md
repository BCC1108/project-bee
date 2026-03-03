# Project BEE

**Cryptocurrency Trading & Backtesting Framework** - 一个功能完整的加密货币量化交易和回测系统

## 📊 特性

- **多策略支持**: BBands (布林带)、MACD、BBI 等技术指标
- **高效回测**: 基于 Vectorbt 的高性能回测引擎
- **实盘交易**: 直接集成 OKX 交易所 API，支持模拟/实盘切换
- **参数优化**: 支持大规模并行参数扫描和优化
- **可视化分析**: 基于 Plotly + Dash 的交互式图表和仪表板
- **风险管理**: 内置止盈止损 (TP/SL) 和头寸管理
- **数据缓存**: 基于 joblib 的聪慧缓存机制，提升计算速度

## 🚀 快速开始

### 1. 环境配置

`ash
git clone https://gitee.com/baronfkingCEE/project-bee.git
cd project-bee

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
`

### 2. 配置 API 密钥

`ash
copy config.ini.template config.ini
`

编辑 config.ini，填入你的 OKX API 密钥。**不要向仓库提交 config.ini**

### 3. 运行示例

`ash
python examples/run.py
`

## 📁 项目结构

`
project-bee/
 project_bee/           # 核心包
    core/             # 策略与信号生成
    data/             # 数据处理
    execution/        # 实盘交易
    visualization/    # 可视化
    config/           # 配置管理
 examples/             # 示例脚本
 tests/               # 单元测试
 docs/                # 文档
 requirements.txt     # 依赖
 README.md           # 本文件
`

## 📚 支持的策略

| 策略 | 指标 | 描述 |
|------|------|------|
| hq2 | BBands | 布林带突破策略 |
| hq3 | BBands | 改进的布林带策略 |
| hq3.5 | BBands | 布林带 + 带宽限制 |
| hq4 | MACD | MACD 金叉死叉策略 |
| hq5 | BBI | 双线合成指标策略 |

## 📝 许可证

MIT License - 详见 LICENSE 文件
