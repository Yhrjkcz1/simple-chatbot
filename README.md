# Simple Chatbot

一个基于Python的简单聊天机器人项目，具有多响应选择功能。

## 项目简介

Simple Chatbot是一个使用ChatterBot库构建的智能聊天机器人，具有以下特点：
- 可以理解并回应用户的自然语言输入
- 支持每个问题提供多个可能的回答选项
- 基于训练数据集进行学习和回答
- 可以通过DeepSeek API生成更多对话训练数据

## 目录结构

```
simple-chatbot/
├── data0.json         # 基础训练数据集
├── data1.json         # 额外训练数据集
├── data2.json         # 额外训练数据集
├── data4.json         # 额外训练数据集
├── database.sqlite3   # 对话数据库文件
├── generate.py        # 训练数据生成脚本
└── test3.py           # 主要聊天机器人实现文件
```

## 安装依赖

```bash
pip install chatterbot
pip install openai
```

## 使用方法

### 1. 运行聊天机器人

```bash
python test3.py
```

运行 `test3.py` 将启动聊天机器人程序，它会自动从所有 `data*.json` 文件加载对话数据，进行去重处理，然后提供交互式聊天界面。

### 2. 生成新的训练数据

```bash
python generate.py
```

注意：使用`generate.py`前，请确保已设置有效的DeepSeek API密钥。

## 自定义训练数据

可以按照以下格式修改或创建自己的训练数据JSON文件：

```json
[
    ["用户问题", ["回答选项1", "回答选项2", "回答选项3"]],
    ["你好", ["你好!", "嗨!", "您好!"]]
]
```

## 功能介绍

- **多响应选择**：聊天机器人能够为同一个问题提供多个不同的回答选项
- **数据库存储**：使用SQLite数据库保存对话历史和学习进度
- **自定义逻辑适配器**：通过MultiResponseAdapter实现多回答功能
- **批量生成对话数据**：可以使用DeepSeek API自动生成训练数据集
- **多文件语料库支持**：支持读取多个JSON文件的语料库并自动去重，比main分支增强了数据处理能力

### 多文件语料库读取与去重

`test3.py` 是本项目的主要聊天机器人实现文件，它实现了从多个JSON文件中读取训练数据并自动去重的功能。以下是相关核心代码：

```python
def load_all_data_files(pattern='data*.json'):
    all_conversations = []
    seen_questions = set()
    for file_path in glob.glob(pattern):
        conversations = load_json_file(file_path)
        for conv in conversations:
            if len(conv) != 2 or not isinstance(conv[1], list):
                continue
            question = conv[0].strip().lower()
            if question not in seen_questions:
                seen_questions.add(question)
                all_conversations.append(conv)
    return all_conversations
```

这段代码会：
1. 使用 `glob.glob` 匹配所有符合 `data*.json` 模式的文件
2. 逐个加载这些JSON文件中的对话数据
3. 通过 `seen_questions` 集合跟踪已经看到的问题，避免重复
4. 只添加未出现过的对话到最终训练数据中

加载完成后，机器人会对去重后的数据进行统一训练：

```python
# 训练所有 data*.json 文件的内容
all_data_conversations = load_all_data_files('data*.json')
if all_data_conversations:
    train_conversations(all_data_conversations, "data*.json")
```

这种方法使得我们可以轻松地添加新的训练数据文件，而不必担心与现有数据重复。

## 开发者信息

本项目基于ChatterBot库和Python开发，用于学习和研究聊天机器人技术。欢迎贡献代码或提出改进建议。

## 许可证

[MIT](https://choosealicense.com/licenses/mit/)