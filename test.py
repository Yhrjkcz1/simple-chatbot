from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import json
from openai import OpenAI
import re  # 新增正则表达式模块

# === DeepSeek API 密钥 ===
deepseek_api_key = 'sk-0342d7b93b4b4180874b96b42830a1f3'  # 请替换为你的有效API密钥
client = OpenAI(
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com/v1"  # 修正API端点
)

# 初始化 ChatterBot
chatbot = ChatBot(
    'EnglishBot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    logic_adapters=[
        'chatterbot.logic.BestMatch',
        'chatterbot.logic.MathematicalEvaluation',
        'chatterbot.logic.TimeLogicAdapter'
    ],
    database_uri='sqlite:///database.sqlite3'
)

def generate_deepseek_corpus(num_conversations=10):
    try:
        prompt = f"""
        Generate {num_conversations} pairs of user questions and chatbot answers in English for a general-purpose chatbot.
        Focus on casual conversation or general knowledge. Return the result in JSON format with a "conversations" key,
        where each conversation is an array of two strings: [user question, chatbot answer].
        Example format: {{"conversations": [["What's the weather like?", "I'm an AI and don't have real-time data, but I can help you look it up online!"]]}}
        Ensure responses are concise and natural. Avoid markdown formatting.
        """
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000  # 增加token限制确保完整响应
        )
        
        # 使用正则表达式提取JSON内容
        content = response.choices[0].message.content
        json_match = re.search(r'({.*})', content, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        corpus = json.loads(json_match.group(1))
        
        # 验证数据结构
        if not isinstance(corpus, dict) or 'conversations' not in corpus:
            raise ValueError("Invalid JSON structure: missing 'conversations' key")
            
        if len(corpus['conversations']) < num_conversations:
            print(f"Warning: Requested {num_conversations} conversations, got {len(corpus['conversations'])}")
            
        return corpus
    except Exception as e:
        print(f"[DeepSeek Error] {str(e)}")
        return {"conversations": []}

# 获取 DeepSeek 生成的语料库
deepseek_corpus = generate_deepseek_corpus(num_conversations=15)  # 增加生成数量

# 改进的自定义对话格式
custom_conversations = [
    ["Hello!", "Hi there! How can I assist you today?"],
    ["Who are you?", "I'm an AI chatbot created to help with general inquiries!"],
    ["What can you do?", "I can chat, answer questions, and perform basic calculations. Feel free to ask anything!"],
    ["Goodbye", "Have a great day! Don't hesitate to come back if you need more help."]
]

# 创建训练器
list_trainer = ListTrainer(chatbot)

def train_conversations(conversations, source_name="custom"):
    try:
        for conv in conversations:
            if len(conv) != 2:
                print(f"Skipping invalid {source_name} conversation: {conv}")
                continue
            # 显式训练问答对
            list_trainer.train([conv[0], conv[1]])
        print(f"Successfully trained {len(conversations)} {source_name} conversations")
    except Exception as e:
        print(f"Training failed ({source_name}): {str(e)}")

# 训练自定义对话
train_conversations(custom_conversations, "custom")

# 训练 DeepSeek 生成的对话
if deepseek_corpus['conversations']:
    train_conversations(deepseek_corpus['conversations'], "DeepSeek")
else:
    print("Using fallback custom conversations only")

# 改进的交互循环
if __name__ == '__main__':
    print("ChatBot Initialized (Type 'exit' to quit)")
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