#!/usr/bin/env python3
"""
Глубокий инспектор с разворачиванием ссылок.
"""
import sys
import requests
from collections import Counter

TOKEN_PATH = "/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt"

def fetch_object(project_id, object_id, token):
    url = f"https://app.speckle.systems/objects/{project_id}/{object_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    return data[0] if isinstance(data, list) else data

def deep_inspect(project_id: str, object_id: str):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    
    print(f"[deep] Загружаем {project_id}/{object_id} ...")
    root = fetch_object(project_id, object_id, token)
    
    if not root:
        print("Ошибка загрузки корневого объекта")
        return
    
    print(f"\nКорневой объект: {root.get('speckle_type', 'Unknown')}")
    print(f"Имя: {root.get('name', 'N/A')}")
    
    # Разворачиваем elements
    types = Counter()
    references_to_load = []
    
    if 'elements' in root and isinstance(root['elements'], list):
        for elem in root['elements']:
            if isinstance(elem, dict):
                if 'referencedId' in elem:
                    references_to_load.append(elem['referencedId'])
                else:
                    elem_type = elem.get('speckle_type', 'Unknown')
                    types[elem_type] += 1
    
    # Загружаем первые 10 ссылок
    print(f"\nНайдено ссылок: {len(references_to_load)}")
    
    for i, ref_id in enumerate(references_to_load[:10]):
        print(f"\n[{i+1}] Загружаю {ref_id[:16]}...")
        ref_obj = fetch_object(project_id, ref_id, token)
        
        if ref_obj:
            ref_type = ref_obj.get('speckle_type', 'Unknown')
            types[ref_type] += 1
            
            # Показываем структуру
            print(f"  Тип: {ref_type}")
            
            # Для AutoCAD объектов часто есть geometry
            if 'geometry' in ref_obj or 'displayValue' in ref_obj:
                print(f"  Геометрия: есть")
            
            # Слой (для AutoCAD)
            if 'layer' in ref_obj:
                print(f"  Слой: {ref_obj['layer']}")
            
            # Показываем первые 5 ключей
            keys = list(ref_obj.keys())[:10]
            print(f"  Ключи: {', '.join(keys)}")
    
    if len(references_to_load) > 10:
        print(f"\n... и ещё {len(references_to_load) - 10} объектов")
    
    print("\n=== СТАТИСТИКА ТИПОВ ===")
    for obj_type, count in sorted(types.items(), key=lambda x: -x[1]):
        print(f"{obj_type}: {count}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: deep_inspect.py <project_id> <object_id>")
        sys.exit(1)
    
    deep_inspect(sys.argv[1], sys.argv[2])
