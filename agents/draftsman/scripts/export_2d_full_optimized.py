#!/usr/bin/env python3
"""
Полный экспорт 2D-плана (все 1065 объектов) - ОПТИМИЗИРОВАННЫЙ GraphQL.
"""
import requests
import json
import sys

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '1619d895969b83cc67ff70e815e7483d'
OUTPUT_FILE = '/mnt/c/bridge/revit_commands.jsonl'

MIN_SEGMENT_LENGTH = 300  # мм
LEVEL_NAME = "Level 1"
WALL_THICKNESS = 200
DEFAULT_HEIGHT = 3000

with open(TOKEN_PATH) as f:
    TOKEN = f.read().strip()

def fetch_rest(obj_id):
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{obj_id}'
    r = requests.get(url, headers={'Authorization': f'Bearer {TOKEN}'})
    data = r.json()
    return data[0] if isinstance(data, list) else data

def graphql_query(query, variables=None):
    url = 'https://app.speckle.systems/graphql'
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    data = {'query': query}
    if variables: data['variables'] = variables
    r = requests.post(url, headers=headers, json=data)
    return r.json()

print("=== ПОЛНЫЙ ЭКСПОРТ 2D-ПЛАНА (OPTIMIZED) ===\n")

# Загружаем структуру
root = fetch_rest(ROOT_OBJECT_ID)
layer_ref = root['elements'][0]['referencedId']

# Вместо загрузки каждого объекта по одному (1065 запросов), 
# попробуем получить все данные через 1 GraphQL запрос.
print(f"Загружаю слой {layer_ref}...")

query = """
query GetObjectTree($projectId: String!, $objectId: String!) {
  project(id: $projectId) {
    object(id: $objectId) {
      children(limit: 1500) {
        objects {
          id
          data
        }
      }
    }
  }
}
"""

res = graphql_query(query, {"projectId": PROJECT_ID, "objectId": layer_ref})

if 'errors' in res:
    print(f"GraphQL Error: {res['errors']}")
    sys.exit(1)

try:
    objects = res['data']['project']['object']['children']['objects']
    print(f"Успешно загружено {len(objects)} объектов через GraphQL!\n")
except Exception as e:
    print(f"Ошибка парсинга ответа: {e}")
    sys.exit(1)

walls = []
all_x = []
all_y = []

for i, obj_wrapper in enumerate(objects):
    obj = obj_wrapper['data']
    obj_type = obj.get('speckle_type', '')
    
    if 'Polycurve' not in obj_type:
        continue
    
    segments = obj.get('segments', [])
    if not segments:
        continue
    
    # Каждый сегмент полилинии → стена
    for seg in segments:
        start = seg.get('start')
        end = seg.get('end')
        
        if not start or not end:
            continue
        
        # Координаты: Speckle говорит 'm', но данные уже в миллиметрах!
        x1 = start['x']
        y1 = start['y']
        x2 = end['x']
        y2 = end['y']
        
        length = seg.get('length', 0)
        
        if length < MIN_SEGMENT_LENGTH:
            continue
        
        all_x.extend([x1, x2])
        all_y.extend([y1, y2])
        
        # Тип стены
        wall_type = "exterior" if length > 3000 else "interior"
        
        walls.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "length": length,
            "type": wall_type
        })

print(f"Найдено стеновых сегментов: {len(walls)}\n")

if not walls:
    print("❌ Не найдено стен")
    sys.exit(1)

# Сдвиг к началу
offset_x = min(all_x)
offset_y = min(all_y)

print(f"Сдвиг координат:")
print(f"  x: {offset_x/1000:.2f} м")
print(f"  y: {offset_y/1000:.2f} м\n")

commands = []

for w in walls:
    cmd = {
        "command": "wall",
        "x1_mm": int(w['x1'] - offset_x),
        "y1_mm": int(w['y1'] - offset_y),
        "x2_mm": int(w['x2'] - offset_x),
        "y2_mm": int(w['y2'] - offset_y),
        "thickness_mm": WALL_THICKNESS,
        "height_mm": DEFAULT_HEIGHT,
        "type": w['type'],
        "level": LEVEL_NAME
    }
    commands.append(cmd)

# Сохраняем
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for cmd in commands:
        f.write(json.dumps(cmd, ensure_ascii=False) + '\n')

print(f"Сохранено: {OUTPUT_FILE}")
print(f"Команд: {len(commands)}\n")

# Статистика
exterior = [c for c in commands if c['type'] == 'exterior']
interior = [c for c in commands if c['type'] == 'interior']

print("=== СТАТИСТИКА ===")
print(f"Всего стен: {len(commands)}")
print(f"  Exterior (длина > 3м): {len(exterior)}")
print(f"  Interior (длина ≤ 3м): {len(interior)}\n")

print("=== ПЕРВЫЕ 3 КОМАНДЫ ===\n")
for cmd in commands[:3]:
    print(json.dumps(cmd, indent=2, ensure_ascii=False))
    print()

print("🎯 Готово к импорту в Revit!")
