from openai import OpenAI
import json
import re
import os

# DeepSeek API 密钥
deepseek_api_key = 'sk-0342d7b93b4b4180874b96b42830a1f3'  # 替换为你的有效API密钥
client = OpenAI(
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com/v1"
)

def generate_deepseek_corpus(num_conversations=50):
    """生成对话语料库"""
    try:
        batch_size = 25
        all_conversations = []
        for batch in range(0, num_conversations, batch_size):
            current_batch = min(batch_size, num_conversations - batch)
            prompt = f"""
            Generate {current_batch} pairs of user questions and chatbot answers in English for a general-purpose chatbot.
            Cover diverse topics like daily life, technology, entertainment, and math queries.
            For each question, provide exactly 3 possible answers to allow multiple response options.
            Return the result in JSON format with a "conversations" key, where each conversation is an array of [user question, [answer1, answer2, answer3]].
            Example format: {{"conversations": [["What's the weather like?", ["It's sunny today!", "I don't have real-time data", "Looks like a great day!"]], ...]}}
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

def save_json_file(data, file_path):
    """保存数据到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"成功保存数据到 {file_path}")
    except Exception as e:
        print(f"保存文件错误: {str(e)}")

def main():
    # 生成对话数据
    num_conversations = 500  # 生成500个对话
    corpus = generate_deepseek_corpus(num_conversations)
    
    # 保存到文件
    output_file = "conversations.json"
    save_json_file(corpus, output_file)
    
    # 打印部分结果预览
    print("\n生成的部分对话预览:")
    for i, conv in enumerate(corpus["conversations"][:3]):
        print(f"\n问题 {i+1}: {conv[0]}")
        for j, ans in enumerate(conv[1]):
            print(f"  回答 {j+1}: {ans}")

if __name__ == "__main__":
    main()