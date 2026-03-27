#!/usr/bin/env python3
"""
Анализатор AutoCAD модели из Speckle.
"""
import requests
from collections import Counter

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'

def fetch_object(project_id, object_id, token):
    url = f'https://app.speckle.systems/objects/{project_id}/{object_id}'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    return data[0] if isinstance(data, list) else data

def analyze():
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    
    project_id = '30eb4c8084'
    
    # Загружаем корень
    root = fetch_object(project_id, '0f9e9c5ff1c0ec1e1d5241208549b264', token)
    layer_id = root['elements'][0]['referencedId']
    
    # Загружаем слой
    layer = fetch_object(project_id, layer_id, token)
    object_ids = [elem['referencedId'] for elem in layer['elements']]
    
    print(f"=== АНАЛИЗ AutoCAD МОДЕЛИ ===\n")
    print(f"Файл: {root['name']}")
    print(f"Слой: {layer['name']}")
    print(f"Объектов в слое: {len(object_ids)}\n")
    
    # Загружаем все объекты
    types = Counter()
    objects_data = []
    
    for i, obj_id in enumerate(object_ids):
        obj = fetch_object(project_id, obj_id, token)
        if obj:
            obj_type = obj.get('speckle_type', 'Unknown')
            types[obj_type] += 1
            objects_data.append(obj)
            
            # Показываем детали
            print(f"[{i+1}] {obj_type}")
            
            if 'area' in obj:
                print(f"    Площадь: {obj['area'] / 1_000_000:.2f} м²")
            
            if 'length' in obj:
                print(f"    Длина: {obj['length'] / 1000:.2f} м")
            
            if 'units' in obj:
                print(f"    Единицы: {obj['units']}")
            
            # Ключи
            keys = [k for k in obj.keys() if not k.startswith('_')]
            print(f"    Ключи: {', '.join(keys[:8])}")
            print()
    
    print("\n=== СТАТИСТИКА ТИПОВ ===")
    for obj_type, count in sorted(types.items(), key=lambda x: -x[1]):
        print(f"{obj_type}: {count}")

if __name__ == "__main__":
    analyze()
