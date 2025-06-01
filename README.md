# Simple Chatbot

这是一个基于ChatterBot框架的简易聊天机器人项目，支持自定义对话训练和DeepSeek API对话生成功能。

> 💡 **提示**：在 `dev` 分支中还提供了一种新的对话数据加载方式，欢迎切换分支体验更多功能。

## 功能特点

- 基于ChatterBot的英语对话机器人
- 支持多种回复选项的自定义逻辑适配器
- 从JSON文件加载和训练对话数据
- 使用DeepSeek API生成丰富的对话语料库
- 自动合并和去重对话数据
- 交互式命令行界面

## 安装要求

- Python 3.6+
- ChatterBot库
- OpenAI客户端（用于DeepSeek API）

```bash
pip install chatterbot==1.0.4 openai
```

## 文件说明

- `test.py` - 主要的聊天机器人实现和交互界面
- `generate.py` - 使用DeepSeek API生成对话语料库
- `conversations.json` - 存储自定义对话数据
- `deepseek_corpus1.json` - DeepSeek生成的对话语料
- `database.sqlite3` - ChatterBot使用的SQLite数据库

## 使用方法

### 1. 生成对话语料库

```bash
python generate.py
```

这将使用DeepSeek API生成对话语料库并保存到`conversations.json`文件。

### 2. 启动聊天机器人

```bash
python test.py
```

程序会自动加载对话数据并进行训练，然后启动交互式对话界面。

### 3. 与机器人对话

启动后，在命令行输入问题，机器人将给出回复。输入"exit"或"quit"退出程序。

## 自定义对话数据

`conversations.json`文件使用以下格式存储对话数据：

```json
[
  ["问题1", ["回答1", "回答2", "回答3"]],
  ["问题2", ["回答1", "回答2", "回答3"]]
]
```

每个对话包含一个问题和多个可能的回答选项。

## 注意事项

- 首次运行时需要设置有效的DeepSeek API密钥
- 训练大量对话可能需要一些时间
- 对话数据会自动去重以避免重复训练

## 许可证

MIT