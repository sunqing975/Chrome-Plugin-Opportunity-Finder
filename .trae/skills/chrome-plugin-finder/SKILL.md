---
name: "chrome-plugin-finder"
description: "Chrome插件机会发现器项目助手。帮助用户理解项目结构、执行爬虫、分析评论、生成产品机会、导出数据和可视化。Invoke when user asks about Chrome plugin opportunity finder, web scraping, LLM analysis, data visualization, or project structure."
---

# Chrome插件机会发现器

## 项目简介

这是一个Chrome插件市场分析工具，通过爬取Chrome Web Store的插件数据，分析用户评论，使用LLM生成产品机会，帮助发现潜在的创业机会。

## 核心能力

### 1. 数据爬取
- 使用Playwright爬取Chrome Web Store插件数据
- 支持反封策略（随机延迟、User-Agent轮换）
- 爬取字段：名称、评分、安装数、评论数、开发者、版本、更新日期等

### 2. 评论分析
- 使用LLM（DeepSeek/百炼方舟/OpenAI）分析用户评论
- 提取痛点、缺失功能、改进机会
- 支持批量分析

### 3. 产品机会生成
- 基于评论分析结果生成创新产品想法
- 生成8个维度：产品想法、核心功能、目标用户、商业模式、开发难度、评分系统、成功因素、风险提示

### 4. 数据导出
- 导出到Excel（plugin_opportunities.xlsx）
- 包含完整的产品机会报告

### 5. 数据可视化
- 评分分布图
- 安装数/评论数分布图
- 产品机会评分分布
- Top 10产品机会
- 痛点词云
- 缺失功能词云

## 项目结构

```
chrome-plugin-finder/
├── main.py                    # 主入口
├── config.py                  # 配置文件
├── agent.md                   # Agent指南
├── crawler/                   # 爬虫模块
│   └── working_crawler.py     # 主爬虫
├── analyzer/                  # 分析模块
│   ├── comment_analyzer.py    # 评论分析
│   └── product_opportunity_generator.py  # 产品机会生成
├── storage/                   # 存储模块
│   ├── db_manager.py          # 数据库管理
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

## 常用命令

### 数据爬取
```bash
# 爬取插件数据
python crawler/working_crawler.py
```

### 数据分析
```bash
# 分析所有插件的评论
python main.py --analyze

# 生成所有插件的产品机会
python main.py --generate
```

### 数据导出
```bash
# 导出到Excel
python main.py --export
```

### 数据可视化
```bash
# 生成可视化图表
python main.py --visualize
```

### 执行完整流程
```bash
# 执行爬取→分析→生成→导出→可视化的完整流程
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

## 数据库表结构

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

## 配置说明

### config.py关键配置

```python
# 插件筛选条件
PLUGIN_FILTER = {
    'min_users': 10000,      # 最小用户数
    'min_rating': 3.5,       # 最小评分
    'min_reviews': 50,       # 最小评论数
}

# LLM API配置
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

## 工作流程

1. **数据爬取**: 使用Playwright爬取Chrome Web Store插件数据
2. **评论抓取**: 抓取每个插件的用户评论
3. **评论分析**: 使用LLM分析评论，提取痛点和改进机会
4. **机会生成**: 基于分析结果生成产品机会
5. **数据导出**: 导出到Excel
6. **数据可视化**: 生成各种图表

## 注意事项

1. **API密钥**: 需要在config.py中配置LLM API密钥
2. **数据量**: 大量数据分析可能需要较长时间
3. **反封策略**: 爬虫已内置随机延迟和User-Agent轮换
4. **日志**: 所有操作记录在logs/目录下

## 扩展开发

### 添加新的分析维度
1. 修改analyzer/comment_analyzer.py中的分析Prompt
2. 更新数据库表结构（如果需要存储新字段）
3. 更新Excel导出和可视化模块

### 添加新的可视化图表
1. 在utils/visualizer.py中添加新的绘图函数
2. 在generate_all_visualizations()中调用新函数

### 集成新的LLM提供商
1. 在utils/llm_client.py中添加新的提供商支持
2. 在config.py中添加配置
