# Chrome插件机会发现器 - Agent指南

## 项目概述

本项目是一个Chrome插件市场分析工具，通过爬取Chrome Web Store的插件数据，分析用户评论，生成产品机会，帮助发现潜在的创业机会。

## 核心功能模块

### 1. 爬虫模块 (`crawler/`)
- **working_crawler.py**: 主爬虫，使用Playwright爬取插件数据
- 支持反封策略（随机延迟、User-Agent轮换）
- 爬取字段：名称、评分、安装数、评论数、开发者、版本、更新日期等

### 2. 分析模块 (`analyzer/`)
- **comment_analyzer.py**: 评论分析，使用LLM提取痛点、缺失功能、改进机会
- **product_opportunity_generator.py**: 产品机会生成，基于分析结果生成创新产品想法

### 3. 存储模块 (`storage/`)
- **db_manager.py**: SQLite数据库管理
- **excel_writer.py**: Excel导出功能
- 数据表：plugins, reviews, analysis_results, opportunities, analysis_status

### 4. 工具模块 (`utils/`)
- **llm_client.py**: LLM客户端（支持DeepSeek、百炼方舟、OpenAI）
- **logger.py**: 日志系统
- **data_viewer.py**: 数据预览
- **visualizer.py**: 数据可视化
- **anti_block.py**: 反封策略

## 数据库结构

### plugins表
- id, plugin_id, name, category, rating, install_count, review_count
- developer, version, last_updated, url, collected_at

### reviews表
- id, plugin_id, author, rating, content, date

### analysis_results表
- id, plugin_id, pain_points, missing_features, improvement_opportunities

### opportunities表
- id, plugin_id, idea, features, target_users, business_model, difficulty
- scores (market_demand, competition, ease_of_building, monetization_potential, overall_score)

### analysis_status表
- plugin_id, reviews_fetched, review_analyzed, opportunity_generated, last_updated

## 常用命令

```bash
# 爬取插件数据
python crawler/working_crawler.py

# 分析评论
python main.py --analyze

# 生成产品机会
python main.py --generate

# 导出到Excel
python main.py --export

# 生成可视化
python main.py --visualize

# 执行完整流程
python main.py --all

# 查看数据
python main.py --show-plugins --limit 10
python main.py --show-reviews 1 --limit 5
python main.py --show-analysis 1
python main.py --show-opportunity 1
python main.py --show-top
```

## 配置说明

### config.py关键配置
- **PLUGIN_FILTER**: 插件筛选条件（最小用户数、评分、评论数）
- **LLM_CONFIG**: LLM API配置（DeepSeek、百炼方舟、OpenAI）
- **EXCEL_CONFIG**: Excel输出配置
- **CRAWLER_CONFIG**: 爬虫配置

## 开发规范

1. **代码注释**: 函数级注释，包含参数、返回值、异常说明，使用中文
2. **错误处理**: 使用try-except块，记录错误日志
3. **数据库操作**: 使用参数化查询防止SQL注入
4. **日志记录**: 使用utils/logger.py记录关键操作

## 文件位置

- 主入口: `main.py`
- 数据库: `plugin_opportunities.db`
- Excel输出: `plugin_opportunities.xlsx`
- 可视化图表: `visualizations/`
- 日志文件: `logs/`

## 注意事项

1. 爬虫需要配置正确的Chrome Web Store URL
2. LLM API需要配置正确的API密钥
3. 数据量较大时，分析和生成操作可能需要较长时间
4. 建议定期备份数据库文件
