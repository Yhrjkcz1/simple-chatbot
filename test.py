from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import json
from openai import OpenAI
import re
import random
import os
import logging

# 禁用 ChatterBot 的详细日志
logging.getLogger('chatterbot').setLevel(logging.WARNING)

# === DeepSeek API 密钥 ===
deepseek_api_key = 'sk-0342d7b93b4b4180874b96b42830a1f3'  # 请替换为你的有效API密钥
client = OpenAI(
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com/v1"
)

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

def generate_deepseek_corpus(num_conversations=50):
    try:
        batch_size = 25
        all_conversations = []
        for batch in range(0, num_conversations, batch_size):
            current_batch = min(batch_size, num_conversations - batch)
            prompt = f"""
            Generate {current_batch} pairs of user questions and chatbot answers in English for a general-purpose chatbot.
            Cover diverse topics like daily life, technology, entertainment, and math queries.
            For each question, provide 2-3 possible answers to allow multiple response options.
            Return the result in JSON format with a "conversations" key, where each conversation is an array of [user question, [answer1, answer2, ...]].
            Example format: {{"conversations": [["What's the weather like?", ["It's sunny today!", "I don't have real-time data, but check a weather app!", "Looks like a great day!"]]}}
            Ensure responses are concise, natural, and varied. Avoid markdown formatting.
            """
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if not json_match:
                raise ValueError(f"No JSON found in response for batch {batch//batch_size + 1}")
            
            corpus = json.loads(json_match.group(1))
            
            if not isinstance(corpus, dict) or 'conversations' not in corpus:
                raise ValueError(f"Invalid JSON structure in batch {batch//batch_size + 1}: missing 'conversations' key")
                
            all_conversations.extend(corpus['conversations'])
        
        if len(all_conversations) < num_conversations:
            print(f"Warning: Requested {num_conversations} conversations, got {len(all_conversations)}")
            
        return {"conversations": all_conversations}
    except Exception as e:
        print(f"[DeepSeek Error] {str(e)}")
        return {"conversations": []}

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

def append_deepseek_to_custom(deepseek_file='deepseek_corpus.json', custom_file='custom_conversations.json'):
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

# 生成新的 DeepSeek 语料（可选）
generate_new_corpus = True  # 设置为 True 以生成新的 20 个对话
if generate_new_corpus:
    deepseek_corpus = generate_deepseek_corpus(num_conversations=20)
    save_json_file(deepseek_corpus['conversations'], 'deepseek_corpus.json')
else:
    deepseek_corpus = {"conversations": load_json_file('deepseek_corpus.json')}

# 训练自定义对话
if custom_conversations:
    train_conversations(custom_conversations, "custom")

# 训练 DeepSeek 生成的对话
if deepseek_corpus['conversations']:
    train_conversations(deepseek_corpus['conversations'], "DeepSeek")

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