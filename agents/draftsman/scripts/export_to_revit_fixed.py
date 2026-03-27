#!/usr/bin/env python3
"""
Экспорт в правильный формат Revit Bridge.
"""
import json

INPUT_FILE = '/home/axis/openclaw/agents/draftsman/temp/walls_grouped.json'
OUTPUT_FILE = '/mnt/c/bridge/revit_commands.jsonl'

MIN_WALL_HEIGHT = 2000  # мм
LEVEL_NAME = "Level 1"

def main():
    with open(INPUT_FILE) as f:
        data = json.load(f)
    
    walls = data['walls']
    
    # Фильтр: высота > 2м
    valid_walls = [w for w in walls if w['height'] > MIN_WALL_HEIGHT]
    
    print(f"Всего стен: {len(walls)}")
    print(f"Валидных (высота > 2м): {len(valid_walls)}\n")
    
    # Находим минимальные координаты для сдвига
    all_x = [w['x_min'] for w in valid_walls] + [w['x_max'] for w in valid_walls]
    all_y = [w['y_min'] for w in valid_walls] + [w['y_max'] for w in valid_walls]
    
    offset_x = min(all_x)
    offset_y = min(all_y)
    
    print(f"Сдвиг координат:")
    print(f"  offset_x: {offset_x:.0f} мм")
    print(f"  offset_y: {offset_y:.0f} мм\n")
    
    commands = []
    
    for wall in valid_walls:
        nx, ny, nz = wall['normal']
        
        # Определяем начало и конец стены
        if abs(nx) > 0.7:
            # Стена параллельна Y
            x1 = wall['x_min'] if nx > 0 else wall['x_max']
            x2 = x1
            y1 = wall['y_min']
            y2 = wall['y_max']
        elif abs(ny) > 0.7:
            # Стена параллельна X
            x1 = wall['x_min']
            x2 = wall['x_max']
            y1 = wall['y_min'] if ny > 0 else wall['y_max']
            y2 = y1
        else:
            # Диагональ
            x1 = wall['x_min']
            y1 = wall['y_min']
            x2 = wall['x_max']
            y2 = wall['y_max']
        
        # Сдвиг к началу координат
        x1_shifted = int(x1 - offset_x)
        y1_shifted = int(y1 - offset_y)
        x2_shifted = int(x2 - offset_x)
        y2_shifted = int(y2 - offset_y)
        
        # Определяем тип стены (по высоте)
        wall_type = "exterior" if wall['height'] > 2700 else "interior"
        
        cmd = {
            "command": "wall",
            "x1_mm": x1_shifted,
            "y1_mm": y1_shifted,
            "x2_mm": x2_shifted,
            "y2_mm": y2_shifted,
            "thickness_mm": 200,
            "height_mm": int(wall['height']),
            "type": wall_type,
            "level": LEVEL_NAME
        }
        
        commands.append(cmd)
    
    # Сохраняем
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for cmd in commands:
            f.write(json.dumps(cmd, ensure_ascii=False) + '\n')
    
    print(f"Сохранено: {OUTPUT_FILE}")
    print(f"Команд: {len(commands)}\n")
    
    # Показываем первые 5
    print("=== ПЕРВЫЕ 5 КОМАНД ===\n")
    for cmd in commands[:5]:
        print(json.dumps(cmd, indent=2, ensure_ascii=False))
        print()

if __name__ == "__main__":
    main()
