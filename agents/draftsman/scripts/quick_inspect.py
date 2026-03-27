#!/usr/bin/env python3
"""
Быстрый инспектор через REST API.
"""
import sys
import requests

TOKEN_PATH = "/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt"

def quick_inspect(project_id: str, object_id: str):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    
    url = f"https://app.speckle.systems/objects/{project_id}/{object_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"[quick] Загружаем {project_id}/{object_id} ...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    data = response.json()
    
    # API возвращает список
    if isinstance(data, list):
        data = data[0] if data else {}
    
    print("\n=== СТРУКТУРА ОБЪЕКТА ===")
    print(f"speckle_type: {data.get('speckle_type', 'N/A')}")
    print(f"totalChildrenCount: {data.get('totalChildrenCount', 0)}")
    
    # Ключи первого уровня
    print("\nКлючи первого уровня:")
    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, list):
            print(f"  {key}: список [{len(value)} элементов]")
        elif isinstance(value, dict):
            print(f"  {key}: объект")
        else:
            print(f"  {key}: {type(value).__name__}")
    
    # Если есть коллекции
    for key in ['elements', '@elements', 'displayValue', '@displayValue']:
        if key in data and isinstance(data[key], list):
            print(f"\n=== {key} ===")
            for i, item in enumerate(data[key][:5]):  # первые 5
                if isinstance(item, dict):
                    print(f"  [{i}] {item.get('speckle_type', type(item))}")
                else:
                    print(f"  [{i}] {item}")
            if len(data[key]) > 5:
                print(f"  ... и ещё {len(data[key]) - 5}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: quick_inspect.py <project_id> <object_id>")
        sys.exit(1)
    
    quick_inspect(sys.argv[1], sys.argv[2])
