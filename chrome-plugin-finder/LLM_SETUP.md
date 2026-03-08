# LLM配置说明

本项目支持多个LLM提供商：DeepSeek、百炼方舟、OpenAI。

## 配置步骤

### 1. 设置API密钥

编辑 `.env` 文件，填入对应的API密钥：

```bash
# DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 百炼方舟API密钥
BAILIAN_API_KEY=your_bailian_api_key_here

# OpenAI API密钥
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 选择LLM提供商

编辑 `config.py` 文件，修改 `LLM_CONFIG` 中的 `provider` 字段：

```python
LLM_CONFIG = {
    'provider': 'deepseek',  # 可选: 'deepseek', 'bailian', 'openai'
    # ... 其他配置
}
```

## 各提供商配置说明

### DeepSeek

- **API密钥获取**: https://platform.deepseek.com/
- **Base URL**: https://api.deepseek.com/v1
- **模型**: deepseek-chat
- **环境变量**: DEEPSEEK_API_KEY

### 百炼方舟（阿里云）

- **API密钥获取**: https://dashscope.aliyuncs.com/
- **Base URL**: https://dashscope.aliyuncs.com/compatible-mode/v1
- **模型**: qwen-plus
- **环境变量**: BAILIAN_API_KEY

### OpenAI

- **API密钥获取**: https://platform.openai.com/
- **Base URL**: https://api.openai.com/v1
- **模型**: gpt-3.5-turbo
- **环境变量**: OPENAI_API_KEY

## 使用示例

### 使用DeepSeek

1. 在 `.env` 文件中设置 `DEEPSEEK_API_KEY`
2. 在 `config.py` 中设置 `provider: 'deepseek'`
3. 运行程序

### 使用百炼方舟

1. 在 `.env` 文件中设置 `BAILIAN_API_KEY`
2. 在 `config.py` 中设置 `provider: 'bailian'`
3. 运行程序

### 使用OpenAI

1. 在 `.env` 文件中设置 `OPENAI_API_KEY`
2. 在 `config.py` 中设置 `provider: 'openai'`
3. 运行程序

## 注意事项

1. 确保API密钥正确，否则会调用失败
2. 不同的提供商可能有不同的调用限制和费用
3. 建议先使用DeepSeek或百炼方舟，因为它们相对便宜
4. 如果某个提供商调用失败，可以尝试切换到其他提供商

## 虚拟环境使用

项目已创建虚拟环境 `venv`，使用方法：

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行程序
python chrome-plugin-finder/main.py

# 退出虚拟环境
deactivate
```

## 依赖安装

依赖已安装在虚拟环境中，如果需要重新安装：

```bash
source venv/bin/activate
pip install -r chrome-plugin-finder/requirements.txt
```
