from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import json
import random
import os
import logging

# 禁用 ChatterBot 的详细日志
logging.getLogger('chatterbot').setLevel(logging.WARNING)

# 自定义逻辑适配器以支持多回答选择
from chatterbot.logic import LogicAdapter
class MultiResponseAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        self.responses = {}  # 存储问题到多个回答的映射

    def can_process(self, statement):
        return statement.text.lower() in self.responses

    def process(self, statement, additional_response_selection_parameters=None):
        from chatterbot.conversation import Statement
        response_text = random.choice(self.responses[statement.text.lower()])
        response = Statement(text=response_text)
        response.confidence = 1.0
        return response

def load_json_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict) or 'conversations' not in data:
                raise ValueError(f"Invalid JSON structure in {file_path}: missing 'conversations' key")
            return data['conversations']
        return []
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return []

def save_json_file(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"conversations": data}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving {file_path}: {str(e)}")

def append_deepseek_to_custom(deepseek_file='deepseek_corpus1.json', custom_file='conversations.json'):
    # 加载 DeepSeek 语料
    deepseek_conversations = load_json_file(deepseek_file)
    
    if deepseek_conversations:
        # 加载自定义语料
        custom_conversations = load_json_file(custom_file)
        
        # 去重：避免重复对话
        existing_questions = {conv[0].lower() for conv in custom_conversations}
        unique_conversations = [conv for conv in deepseek_conversations if conv[0].lower() not in existing_questions]
        custom_conversations.extend(unique_conversations)
        
        # 保存更新后的自定义语料
        save_json_file(custom_conversations, custom_file)
        
        # 清空 DeepSeek 语料文件
        save_json_file([], deepseek_file)
        
        return custom_conversations
    else:
        return load_json_file(custom_file)

def train_conversations(conversations, source_name="custom"):
    try:
        # 查找 MultiResponseAdapter
        multi_response_adapter = None
        for adapter in chatbot.logic_adapters:
            if isinstance(adapter, MultiResponseAdapter):
                multi_response_adapter = adapter
                break
        if not multi_response_adapter:
            raise ValueError("MultiResponseAdapter not found in logic adapters")
        
        for conv in conversations:
            if len(conv) != 2 or not isinstance(conv[1], list):
                print(f"Skipping invalid {source_name} conversation: {conv}")
                continue
            # 存储多回答到自定义适配器（使用小写问题以统一匹配）
            multi_response_adapter.responses[conv[0].lower()] = conv[1]
            # 训练 BestMatch 适配器（仅使用第一个回答）
            list_trainer.train([conv[0], conv[1][0]])
    except Exception as e:
        print(f"Training failed ({source_name}): {str(e)}")

# 初始化 ChatterBot
chatbot = ChatBot(
    'EnglishBot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    logic_adapters=[
        {
            'import_path': '__main__.MultiResponseAdapter',
            'maximum_similarity_threshold': 0.95
        },
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'maximum_similarity_threshold': 0.90
        },
        {
            'import_path': 'chatterbot.logic.MathematicalEvaluation'
        },
        {
            'import_path': 'chatterbot.logic.TimeLogicAdapter'
        }
    ],
    database_uri='sqlite:///database.sqlite3',
    preprocessors=[
        'chatterbot.preprocessors.clean_whitespace',
        'chatterbot.preprocessors.convert_to_ascii'
    ]
)

# 创建训练器，禁用训练进度条
list_trainer = ListTrainer(chatbot, show_training_progress=False)

# 追加 DeepSeek 语料到自定义语料并清空 DeepSeek 文件
custom_conversations = append_deepseek_to_custom('deepseek_corpus.json', 'custom_conversations.json')

# 训练自定义对话
if custom_conversations:
    train_conversations(custom_conversations, "custom")

# 训练 DeepSeek 语料（如果存在）
deepseek_conversations = load_json_file('deepseek_corpus.json')
if deepseek_conversations:
    train_conversations(deepseek_conversations, "DeepSeek")

# 交互循环
if __name__ == '__main__':
    print("ChatBot Initialized (Type 'exit' to quit)")
    try:
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                response = chatbot.get_response(user_input)
                print(f"Bot: {response}")
            
            except (KeyboardInterrupt, EOFError):
                print("\nSession ended")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    finally:
        print("Script terminated")