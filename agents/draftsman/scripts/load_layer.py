#!/usr/bin/env python3
import requests
import sys

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'

def load_layer(project_id, layer_id):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    
    url = f'https://app.speckle.systems/objects/{project_id}/{layer_id}'
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Загружаю слой {layer_id}...")
    response = requests.get(url, headers=headers)
    
    print(f"Статус: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Ошибка: {response.text}")
        return
    
    data = response.json()
    data = data[0] if isinstance(data, list) else data
    
    print(f"\nСлой: {data.get('name', 'N/A')}")
    print(f"Тип: {data.get('speckle_type')}")
    
    if 'elements' in data:
        print(f"Элементов в слое: {len(data['elements'])}")
        
        for i, elem in enumerate(data['elements'][:10]):
            if isinstance(elem, dict):
                elem_type = elem.get('speckle_type', 'Unknown')
                print(f"  [{i}] {elem_type}")
                
                if 'referencedId' in elem:
                    print(f"      -> ссылка: {elem['referencedId']}")
                    
                # Показываем ключи
                keys = list(elem.keys())[:8]
                print(f"      ключи: {', '.join(keys)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: load_layer.py <project_id> <layer_id>")
        sys.exit(1)
    
    load_layer(sys.argv[1], sys.argv[2])
