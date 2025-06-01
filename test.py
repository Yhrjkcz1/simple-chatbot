from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import json
import random
import os
import logging

# Disable ChatterBot's verbose logging
logging.getLogger('chatterbot').setLevel(logging.WARNING)

# Custom logic adapter to support multiple response options
from chatterbot.logic import LogicAdapter
class MultiResponseAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        self.responses = {}  # Map questions to multiple responses

    def can_process(self, statement):
        return statement.text.lower() in self.responses

    def process(self, statement, additional_response_selection_parameters=None):
        from chatterbot.conversation import Statement
        response_text = random.choice(self.responses[statement.text.lower()])
        response = Statement(text=response_text)
        response.confidence = 1.0
        return response

def load_json_file(file_path):
    """Load JSON file and validate structure."""
    try:
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist, returning empty conversations")
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict) or 'conversations' not in data:
            raise ValueError(f"Invalid JSON structure in {file_path}: missing 'conversations' key")
        return data['conversations']
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return []

def save_json_file(data, file_path):
    """Save data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"conversations": data}, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved data to {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {str(e)}")

def append_deepseek_to_custom(deepseek_file='deepseek_corpus.json', custom_file='conversations.json'):
    """Append DeepSeek corpus to custom corpus and clear DeepSeek file."""
    try:
        # Load DeepSeek corpus
        deepseek_conversations = load_json_file(deepseek_file)
        if not deepseek_conversations:
            print(f"No conversations found in {deepseek_file}, loading {custom_file}")
            return load_json_file(custom_file)

        # Validate DeepSeek conversations
        for i, conv in enumerate(deepseek_conversations):
            if not (isinstance(conv, list) and len(conv) == 2 and isinstance(conv[0], str) and isinstance(conv[1], list) and len(conv[1]) > 0):
                raise ValueError(f"Invalid conversation format at index {i} in {deepseek_file}: {conv}")

        # Load custom corpus
        custom_conversations = load_json_file(custom_file)

        # Deduplicate conversations
        existing_questions = {conv[0].lower() for conv in custom_conversations}
        unique_conversations = [conv for conv in deepseek_conversations if conv[0].lower() not in existing_questions]
        custom_conversations.extend(unique_conversations)

        # Backup custom file before overwriting
        if os.path.exists(custom_file):
            backup_file = custom_file + '.backup'
            save_json_file(custom_conversations, backup_file)
            print(f"Created backup of {custom_file} at {backup_file}")

        # Save updated custom corpus
        save_json_file(custom_conversations, custom_file)

        # Clear DeepSeek corpus file
        save_json_file([], deepseek_file)

        # Preview merged conversations
        print(f"\nPreview of merged conversations (first 3):")
        for i, conv in enumerate(custom_conversations[:3]):
            print(f"  Conversation {i+1}: Question: {conv[0]}")
            for j, ans in enumerate(conv[1]):
                print(f"    Answer {j+1}: {ans}")

        return custom_conversations
    except Exception as e:
        print(f"Error in append_deepseek_to_custom: {str(e)}")
        return load_json_file(custom_file)

def train_conversations(conversations, source_name="custom"):
    """Train chatbot with conversations."""
    try:
        # Find MultiResponseAdapter
        multi_response_adapter = None
        for adapter in chatbot.logic_adapters:
            if isinstance(adapter, MultiResponseAdapter):
                multi_response_adapter = adapter
                break
        if not multi_response_adapter:
            raise ValueError("MultiResponseAdapter not found in logic adapters")

        valid_conversations = 0
        for i, conv in enumerate(conversations):
            # Validate conversation format
            if not (isinstance(conv, list) and len(conv) == 2 and isinstance(conv[0], str) and isinstance(conv[1], list) and len(conv[1]) > 0):
                print(f"Skipping invalid {source_name} conversation at index {i}: {conv}")
                continue
            # Store multiple responses in adapter
            multi_response_adapter.responses[conv[0].lower()] = conv[1]
            # Train BestMatch with first response
            list_trainer.train([conv[0], conv[1][0]])
            valid_conversations += 1
        print(f"Successfully trained {valid_conversations} {source_name} conversations")
    except Exception as e:
        print(f"Training failed ({source_name}): {str(e)}")

# Initialize ChatterBot
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

# Create trainer, disable training progress bar
list_trainer = ListTrainer(chatbot, show_training_progress=False)

# Load and train custom conversations from conversations.json
custom_conversations = load_json_file('conversations.json')
if custom_conversations:
    print(f"\nLoading custom conversations from conversations.json")
    train_conversations(custom_conversations, "custom")

# Append DeepSeek corpus to custom and train
deepseek_conversations = append_deepseek_to_custom(deepseek_file='deepseek_corpus1.json', custom_file='conversations.json')
if deepseek_conversations:
    print(f"\nTraining merged conversations (including DeepSeek)")
    train_conversations(deepseek_conversations, "merged")

# Interactive loop
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
                print(f"Error processing input: {str(e)}")
    finally:
        print("Script terminated")