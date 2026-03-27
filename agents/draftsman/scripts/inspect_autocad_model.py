#!/usr/bin/env python3
"""
Инспектор AutoCAD DWG модели из Speckle.
Показывает типы объектов и их количество.
"""
import sys
from specklepy.api.client import SpeckleClient
from specklepy.api import operations
from specklepy.transports.server import ServerTransport
from collections import Counter

TOKEN_PATH = "/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt"

def inspect_model(project_id: str, version_id: str):
    # Подключение
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    
    client = SpeckleClient(host="app.speckle.systems")
    client.authenticate_with_token(token)
    
    # Загрузка модели
    print(f"[inspect] Загружаем {project_id} / {version_id} ...")
    transport = ServerTransport(client=client, stream_id=project_id)
    root = operations.receive(obj_id=version_id, remote_transport=transport)
    
    # Собираем типы объектов
    types = Counter()
    
    def walk(obj, depth=0):
        if depth > 10:
            return
        
        obj_type = getattr(obj, 'speckle_type', type(obj).__name__)
        types[obj_type] += 1
        
        # Рекурсивно обходим коллекции
        if hasattr(obj, '__dict__'):
            for key, value in obj.__dict__.items():
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, 'speckle_type'):
                            walk(item, depth + 1)
                elif hasattr(value, 'speckle_type'):
                    walk(value, depth + 1)
    
    walk(root)
    
    # Вывод статистики
    print("\n=== СТАТИСТИКА ОБЪЕКТОВ ===")
    for obj_type, count in sorted(types.items(), key=lambda x: -x[1]):
        print(f"{obj_type}: {count}")
    
    print(f"\nВсего уникальных типов: {len(types)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: inspect_autocad_model.py <project_id> <version_id>")
        sys.exit(1)
    
    inspect_model(sys.argv[1], sys.argv[2])
