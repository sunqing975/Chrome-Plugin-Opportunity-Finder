# 项目配置文件

# 插件筛选条件
PLUGIN_FILTER = {
    'min_users': 10000,      # 最小用户数
    'min_rating': 3.5,       # 最小评分
    'min_reviews': 50,        # 最小评论数
    'categories': [           # 重点分类
        'productivity',
        'marketing',
        'SEO',
        'AI tools',
        'social media',
        'ecommerce'
    ]
}

# 评论筛选条件
REVIEW_FILTER = {
    'max_rating': 3,  # 只分析评分<=3的评论
    'max_reviews': 100  # 每个插件最多分析100条评论
}

# LLM API配置
LLM_CONFIG = {
    'provider': 'deepseek',  # 可选: 'deepseek', 'bailian', 'openai'
    'deepseek': {
        'api_key': 'your_deepseek_api_key',
        'base_url': 'https://api.deepseek.com/v1',
        'model': 'deepseek-chat',
        'temperature': 0.7
    },
    'bailian': {
        'api_key': 'your_bailian_api_key',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'model': 'qwen-plus',
        'temperature': 0.7
    },
    'openai': {
        'api_key': 'your_openai_api_key',
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-3.5-turbo',
        'temperature': 0.7
    }
}

# Excel输出配置
EXCEL_CONFIG = {
    'output_file': 'plugin_opportunities.xlsx',
    'sheet_name': 'Opportunities'
}

# 爬虫配置
CRAWLER_CONFIG = {
    'timeout': 30,
    'headless': True,
    'sleep_time': 2
}
