#!/usr/bin/env python3
"""
Анализ 2D-плана из AutoCAD (Speckle).
"""
import requests
from collections import Counter

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '1619d895969b83cc67ff70e815e7483d'

def fetch(obj_id):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{obj_id}'
    r = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    return data[0] if isinstance(data, list) else data

print("=== АНАЛИЗ 2D-ПЛАНА ===\n")

# Корень
root = fetch(ROOT_OBJECT_ID)
print(f"Файл: {root.get('name', 'N/A')}\n")

# Слой
layer_ref = root['elements'][0]['referencedId']
layer = fetch(layer_ref)
print(f"Слой: {layer.get('name', 'N/A')}")
print(f"Элементов: {len(layer['elements'])}\n")

# Загружаем первые 100 объектов для анализа
print("Анализирую типы объектов (первые 100)...\n")

types = Counter()
polycurves = []
lines = []

for i, elem in enumerate(layer['elements'][:100]):
    obj_ref = elem.get('referencedId')
    if not obj_ref:
        continue
    
    obj = fetch(obj_ref)
    obj_type = obj.get('speckle_type', 'Unknown')
    types[obj_type] += 1
    
    # Сохраняем полилинии
    if 'Polycurve' in obj_type:
        polycurves.append({
            'closed': obj.get('closed', False),
            'length': obj.get('length', 0),
            'area': obj.get('area', 0)
        })
    
    # Сохраняем линии
    if 'Line' in obj_type:
        lines.append({
            'length': obj.get('length', 0)
        })

print("=== ТИПЫ ОБЪЕКТОВ ===\n")
for obj_type, count in sorted(types.items(), key=lambda x: -x[1]):
    print(f"{obj_type}: {count}")

print(f"\n=== ПОЛИЛИНИИ ===\n")
closed_poly = [p for p in polycurves if p['closed']]
print(f"Всего полилиний: {len(polycurves)}")
print(f"Замкнутых: {len(closed_poly)}")

if closed_poly:
    print(f"\nПримеры замкнутых полилиний:")
    for i, p in enumerate(closed_poly[:5]):
        print(f"  [{i+1}] Длина: {p['length']/1000:.2f} м, Площадь: {p['area']/1_000_000:.2f} м²")

print(f"\n=== ЛИНИИ ===\n")
print(f"Всего линий: {len(lines)}")
if lines:
    total_length = sum(l['length'] for l in lines)
    print(f"Общая длина: {total_length/1000:.2f} м")

print("\n✅ Анализ завершён")
