from openai import OpenAI
import json
import re
import os

# DeepSeek API 密钥
deepseek_api_key = ''  # 替换为你的有效API密钥
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
            # prompt = f"""
            # Generate {current_batch} pairs of user questions and chatbot answers in English for a general-purpose chatbot.
            # Cover diverse topics like daily life, technology, entertainment, and math queries.
            # For each question, provide exactly 3 possible answers to allow multiple response options.
            # Return the result in JSON format with a "conversations" key, where each conversation is an array of [user question, [answer1, answer2, answer3]].
            # Example format: {{"conversations": [["What's the weather like?", ["It's sunny today!", "I don't have real-time data", "Looks like a great day!"]], ...]}}
            # Ensure responses are concise, natural, and varied. Avoid markdown formatting.
            # """
            prompt = f"""
            You are an intelligent AI assistant designed to help users in various practical scenarios.

            Generate {current_batch} dialogue pairs between a user and the assistant. Each user question should sound like a natural request for help, advice, or information. The assistant should respond professionally, concisely, and helpfully.

            Topics should include:
            - Productivity and daily planning (e.g., scheduling, prioritizing)
            - Technology support (e.g., coding help, app usage)
            - Everyday problem solving (e.g., how-to questions)
            - Learning and education (e.g., studying tips, summaries)
            - Simple reasoning or explanations (e.g., math or logic)

            For each question, provide exactly 3 varied but reasonable assistant replies to simulate multi-option responses.

            Return the result as JSON with a top-level "conversations" key.
            Each item should be a list of: [user question, [answer1, answer2, answer3]].

            Example format:
            {{"conversations": [["How can I stay focused while studying?", ["Try the Pomodoro technique.", "Limit distractions and set clear goals.", "Use a study timer app to keep on track."]]}}

            Avoid markdown or formatting characters. Ensure all responses are clear, useful, and sound like a capable assistant.
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
    num_conversations = 50  # 生成50个对话
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