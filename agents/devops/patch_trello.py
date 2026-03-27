import re

with open('/home/axis/openclaw/axis-system/trello-webhook/trello-webhook-server.py', 'r') as f:
    content = f.read()

# Fix list_name extraction
old_list_name_code = """        card_name = action.get('data', {}).get('card', {}).get('name', 'Unknown')
        list_name = action.get('data', {}).get('list', {}).get('name', '')
        member = action.get('memberCreator', {}).get('username', 'Unknown')"""

new_list_name_code = """        card_name = action.get('data', {}).get('card', {}).get('name', 'Unknown')
        
        # Determine target list name (handling updateCard list changes)
        list_name = action.get('data', {}).get('list', {}).get('name', '')
        if action_type == 'updateCard' and 'listAfter' in action.get('data', {}):
            list_name = action['data']['listAfter'].get('name', '')
            
        member = action.get('memberCreator', {}).get('username', 'Unknown')"""

content = content.replace(old_list_name_code, new_list_name_code)

# Add logic inside _notify_agents
old_notify_code = """        # Автоиндексация: если карточка перемещена в "Готово"/"Done"
        if list_name and any(done in list_name.lower() for done in ['готово', 'done', 'завершено', 'закрыто']):"""

new_notify_code = """        # ТРИГГЕРЫ ДЛЯ АГЕНТОВ: Draftsman и QC (Задача 17)
        if action_type == 'updateCard' and list_name:
            if list_name == 'In Progress':
                logger.info(f"🚀 Триггер 'In Progress': уведомляем draftsman о задаче {card_name}")
                trigger_msg = f"Новая задача в Trello перешла в 'In Progress': {card_name}. Пожалуйста, ознакомься с ТЗ и приступай к работе."
                subprocess.Popen(
                    ["openclaw", "sessions", "spawn", "draftsman", "--message", trigger_msg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif list_name == 'QC Review':
                logger.info(f"✅ Триггер 'QC Review': уведомляем qc о завершении задачи {card_name}")
                trigger_msg = f"Задача Trello переведена в 'QC Review': {card_name}. Пожалуйста, проведи проверку качества."
                subprocess.Popen(
                    ["openclaw", "sessions", "send", "--label", "qc", "--message", trigger_msg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

        # Автоиндексация: если карточка перемещена в "Готово"/"Done"
        if list_name and any(done in list_name.lower() for done in ['готово', 'done', 'завершено', 'закрыто']):"""

content = content.replace(old_notify_code, new_notify_code)

with open('/home/axis/openclaw/axis-system/trello-webhook/trello-webhook-server.py', 'w') as f:
    f.write(content)
