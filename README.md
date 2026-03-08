# Chrome插件机会发现器

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个智能的Chrome插件市场分析工具，通过爬取Chrome Web Store的插件数据，分析用户评论，使用LLM生成产品机会，帮助发现潜在的创业机会。

## ✨ 核心功能

- 🔍 **智能爬虫**: 使用Playwright爬取Chrome Web Store插件数据，支持反封策略
- 💬 **评论分析**: 使用LLM（DeepSeek/百炼方舟/OpenAI）分析用户评论，提取痛点和改进机会
- 💡 **机会生成**: 基于评论分析生成创新产品想法，包含8个维度的完整评估
- 📊 **数据导出**: 导出到Excel，包含完整的产品机会报告
- 📈 **数据可视化**: 生成评分分布、词云等多种可视化图表
- 🗄️ **数据存储**: 使用SQLite存储所有数据，支持增量更新

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Chrome浏览器

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/yourusername/Chrome-Plugin-Opportunity-Finder.git
   cd Chrome-Plugin-Opportunity-Finder
   ```

2. **创建虚拟环境并安装依赖**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **配置API密钥**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的API密钥
   ```

4. **运行项目**
   ```bash
   cd chrome-plugin-finder
   python main.py --all
   ```

## 📖 使用指南

### 常用命令

```bash
# 爬取插件数据
python crawler/working_crawler.py

# 分析所有插件的评论
python main.py --analyze

# 生成所有插件的产品机会
python main.py --generate

# 导出到Excel
python main.py --export

# 生成可视化图表
python main.py --visualize

# 执行完整流程（爬取→分析→生成→导出→可视化）
python main.py --all
```

### 数据查看

```bash
# 查看插件列表
python main.py --show-plugins --limit 10

# 查看插件评论
python main.py --show-reviews 1 --limit 5

# 查看分析结果
python main.py --show-analysis 1

# 查看产品机会
python main.py --show-opportunity 1

# 查看Top产品机会
python main.py --show-top
```

## 🏗️ 项目结构

```
chrome-plugin-finder/
├── main.py                    # 主入口
├── config.py                  # 配置文件
├── agent.md                   # Agent使用指南
├── crawler/                   # 爬虫模块
│   └── working_crawler.py     # 主爬虫（Playwright）
├── analyzer/                  # 分析模块
│   ├── comment_analyzer.py    # 评论分析
│   └── product_opportunity_generator.py  # 产品机会生成
├── storage/                   # 存储模块
│   ├── db_manager.py          # SQLite数据库管理
│   └── excel_writer.py        # Excel导出
├── utils/                     # 工具模块
│   ├── llm_client.py          # LLM客户端
│   ├── logger.py              # 日志系统
│   ├── data_viewer.py         # 数据预览
│   ├── visualizer.py          # 数据可视化
│   └── anti_block.py          # 反封策略
├── test/                      # 测试脚本
├── logs/                      # 日志文件
├── visualizations/            # 可视化图表
├── plugin_opportunities.db    # SQLite数据库
└── plugin_opportunities.xlsx  # Excel输出
```

## ⚙️ 配置说明

### 插件筛选条件 (config.py)

```python
PLUGIN_FILTER = {
    'min_users': 10000,      # 最小用户数
    'min_rating': 3.5,       # 最小评分
    'min_reviews': 50,       # 最小评论数
    'categories': [          # 重点分类
        'productivity',
        'marketing',
        'SEO',
        'AI tools',
    ]
}
```

### LLM API配置 (config.py)

```python
LLM_CONFIG = {
    'provider': 'deepseek',  # 可选: 'deepseek', 'bailian', 'openai'
    'deepseek': {
        'api_key': 'your_api_key',
        'base_url': 'https://api.deepseek.com/v1',
        'model': 'deepseek-chat',
    },
    'bailian': {
        'api_key': 'your_api_key',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'model': 'qwen-plus',
    }
}
```

## 📊 输出示例

### Excel报告字段

| 字段 | 说明 |
|------|------|
| Plugin Name | 插件名称 |
| Category | 插件分类 |
| Rating | 插件评分 |
| Installs | 安装数量 |
| Reviews | 评论数量 |
| Pain Points | 用户痛点 |
| Missing Features | 缺失功能 |
| Product Idea | 产品想法 |
| Core Features | 核心功能 |
| Target Users | 目标用户 |
| Business Model | 商业模式 |
| Difficulty | 开发难度 |
| Market Demand | 市场需求评分 |
| Competition | 竞争情况评分 |
| Ease of Building | 构建难度评分 |
| Monetization Potential | 盈利潜力评分 |
| Overall Score | 综合评分 |

### 可视化图表

- **rating_distribution.png**: 插件评分分布
- **install_distribution.png**: 安装数分布
- **review_distribution.png**: 评论数分布
- **opportunity_scores.png**: 产品机会评分分布
- **top_10_opportunities.png**: Top 10产品机会
- **pain_points_wordcloud.png**: 痛点词云
- **missing_features_wordcloud.png**: 缺失功能词云

## 🗄️ 数据库结构

### plugins表
存储插件基本信息：id, plugin_id, name, category, rating, install_count, review_count, developer, version, last_updated, url, collected_at

### reviews表
存储用户评论：id, plugin_id, author, rating, content, date

### analysis_results表
存储分析结果：id, plugin_id, pain_points, missing_features, improvement_opportunities

### opportunities表
存储产品机会：id, plugin_id, idea, features, target_users, business_model, difficulty, scores

### analysis_status表
存储分析状态：plugin_id, reviews_fetched, review_analyzed, opportunity_generated, last_updated

## 🛠️ 开发指南

### 添加新的分析维度

1. 修改 `analyzer/comment_analyzer.py` 中的分析Prompt
2. 更新数据库表结构（如果需要存储新字段）
3. 更新Excel导出和可视化模块

### 添加新的可视化图表

1. 在 `utils/visualizer.py` 中添加新的绘图函数
2. 在 `generate_all_visualizations()` 中调用新函数

### 集成新的LLM提供商

1. 在 `utils/llm_client.py` 中添加新的提供商支持
2. 在 `config.py` 中添加配置

## ⚠️ 注意事项

1. **API密钥**: 需要在config.py或.env中配置LLM API密钥
2. **数据量**: 大量数据分析可能需要较长时间，请耐心等待
3. **反封策略**: 爬虫已内置随机延迟和User-Agent轮换，但仍需合理使用
4. **日志**: 所有操作记录在logs/目录下，便于排查问题
5. **费用**: 使用LLM API会产生费用，请注意控制调用次数

## 🤝 贡献指南

1. Fork 本项目
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📝 许可证

本项目采用 [MIT](LICENSE) 许可证

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 强大的浏览器自动化工具
- [OpenAI](https://openai.com/) / [DeepSeek](https://deepseek.com/) / [百炼](https://bailian.aliyun.com/) - LLM服务提供商
- [Pandas](https://pandas.pydata.org/) - 数据处理
- [Matplotlib](https://matplotlib.org/) / [Seaborn](https://seaborn.pydata.org/) - 数据可视化

## 📧 联系方式

如有问题或建议，欢迎提交Issue或联系项目维护者。

---

⭐ 如果这个项目对你有帮助，请给它一个Star！