import os
import json
import re
from datetime import datetime

MONTHS_ES = {
    'january': 'enero',
    'february': 'febrero',
    'march': 'marzo',
    'april': 'abril',
    'may': 'mayo',
    'june': 'junio',
    'july': 'julio',
    'august': 'agosto',
    'september': 'septiembre',
    'october': 'octubre',
    'november': 'noviembre',
    'december': 'diciembre',
}

def get_conversation_messages(conversation):
    """Devuelve los mensajes de una conversación en orden cronológico y con etiquetas legibles."""
    messages = []
    current_node = conversation.get("current_node")
    mapping = conversation.get("mapping", {})
    while current_node:
        node = mapping.get(current_node, {})
        message = node.get("message") if node else None
        content = message.get("content") if message else None
        author = message.get("author", {}).get("role", "") if message else ""
        if content and content.get("content_type") == "text":
            parts = content.get("parts", [])
            if parts and len(parts) > 0 and len(parts[0]) > 0:
                if author != "system" or (message.get("metadata", {}) if message else {}).get("is_user_system_message"):
                    if author == "assistant":
                        author = "🤖 ChatGPT:"
                    elif author == "user":
                        author = "🙍‍♂️ Usuario:"
                    messages.append({"author": author, "text": parts[0]})
        current_node = node.get("parent") if node else None
    return messages[::-1]


def write_conversations_and_json(conversations_data):
    """Procesa las conversaciones y las exporta a archivos Markdown y un resumen JSON."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    created_directories_info = []
    pruned_data = {}
    for conversation in conversations_data:
        updated = conversation.get('update_time')
        if not updated:
            continue
        updated_date = datetime.fromtimestamp(updated)
        month_en = updated_date.strftime('%B').lower()
        month_es = MONTHS_ES.get(month_en, month_en)
        month_num = updated_date.strftime('%m')
        year = updated_date.strftime('%Y')
        directory_name = f"{year}_{month_num}_{month_es}"
        directory_path = os.path.join(output_dir, directory_name)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        title = conversation.get('title', 'Sin título')
        sanitized_title = title
        sanitized_title = re.sub(r'[<>:"/\\|?*]', '_', sanitized_title)
        sanitized_title = sanitized_title.strip('. ')
        sanitized_title = sanitized_title[:120]
        file_name = os.path.join(
            directory_path,
            f"{updated_date.strftime('%Y_%m_%d_%H_%M_%S')}_{sanitized_title}.md"
        )
        messages = get_conversation_messages(conversation)
        with open(file_name, 'w', encoding="utf-8") as file:
            file.write(f"# {title}\n\n")
            for message in messages:
                file.write(f"## {message['author']}\n")
                file.write(f"{message['text']}\n\n")
        if directory_name not in pruned_data:
            pruned_data[directory_name] = []
        pruned_data[directory_name].append({
            "title": title,
            "create_time": datetime.fromtimestamp(conversation.get('create_time')).strftime('%Y-%m-%d %H:%M:%S'),
            "update_time": updated_date.strftime('%Y-%m-%d %H:%M:%S'),
            "messages": messages
        })
        created_directories_info.append({
            "directory": directory_path,
            "file": file_name
        })
    pruned_json_path = os.path.join(output_dir, 'pruned.json')
    with open(pruned_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(pruned_data, json_file, ensure_ascii=False, indent=4)
    return created_directories_info


def main():
    """Ejecuta el procesamiento de las conversaciones desde conversations.json."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    conversations_path = os.path.join(script_dir, 'conversations.json')
    if not os.path.exists(conversations_path):
        print(f"Error: No se encuentra el archivo conversations.json en {script_dir}")
        return
    try:
        with open(conversations_path, 'r', encoding='utf-8') as file:
            conversations_data = json.load(file)
        created_directories_info = write_conversations_and_json(conversations_data)
        print(f"Se han procesado las conversaciones exitosamente.")
        print(f"Los archivos se han guardado en: {os.path.join(script_dir, 'output')}")
    except Exception as e:
        print(f"Error al procesar el archivo: {str(e)}")

if __name__ == "__main__":
    main()
