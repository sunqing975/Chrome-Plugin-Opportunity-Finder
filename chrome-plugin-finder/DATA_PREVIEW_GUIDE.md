# 数据预览功能使用指南

## 问题修复

之前发现数据预览显示空白，原因是：

1. **爬虫选择器失效**：Chrome Web Store页面结构变化，原来的CSS选择器无法提取数据
2. **数据排序问题**：数据库查询默认按install_count排序，新数据都是0，排在后面

## 修复内容

### 1. 更新爬虫模块 (`crawler/plugin_crawler.py`)
- 使用更可靠的元素提取方式（直接通过Selenium查找元素）
- 使用正则表达式从页面文本中提取评分、评论数、安装数等信息
- 添加错误处理和日志输出

### 2. 修复数据排序 (`storage/db_manager.py`)
- 将插件列表查询从 `ORDER BY install_count DESC` 改为 `ORDER BY id DESC`
- 这样新爬取的插件会显示在前面

## 数据预览命令

### 查看插件列表
```bash
python main.py --show-plugins --limit 10
```

### 查看特定插件的评论
```bash
python main.py --show-reviews 37 --limit 5
```

### 查看分析结果
```bash
python main.py --show-analysis 37
```

### 查看产品机会
```bash
python main.py --show-opportunity 37
```

### 查看插件完整信息
```bash
python main.py --show-details 37
```

### 查看最佳产品机会排行
```bash
python main.py --show-top --limit 10
```

## 当前数据状态

数据库中已有插件数据，可以通过预览功能查看：
- ID 37: Ice Dodo
- ID 36: GMass: Powerful mail merge for
- ID 35: Toby: Tab Management Tool
- ID 34: Cheerie - You Search. We Donat
- ID 33: Moonlight：科研论文的AI同伴
- ...等等

## 后续建议

1. **完善爬虫**：当前爬虫只能获取插件名称，评分、用户数等信息提取还不够完善
2. **添加更多数据源**：可以考虑使用Chrome Web Store API或其他数据源
3. **数据清洗**：对爬取的数据进行清洗和标准化处理
