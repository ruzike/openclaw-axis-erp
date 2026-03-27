#!/usr/bin/env python3
"""
Экспорт стен в JSONL для Revit Bridge.
Формат: CreateWall (startX, startY, endX, endY, height, thickness, level)
"""
import json
import math

INPUT_FILE = '/home/axis/openclaw/agents/draftsman/temp/walls_grouped.json'
OUTPUT_FILE = 'C:\\bridge\\revit_commands.jsonl'
OUTPUT_LOCAL = '/home/axis/openclaw/agents/draftsman/temp/revit_commands.jsonl'

def normalize_coordinates(x, y):
    """Нормализует координаты (сдвиг к началу координат)"""
    # Пока без сдвига — координаты абсолютные
    return int(x), int(y)

def generate_wall_command(wall, wall_thickness=200):
    """Генерирует команду CreateWall для Revit"""
    # Определяем начало и конец стены по нормали
    nx, ny, nz = wall['normal']
    
    # Если нормаль направлена вдоль X (nx близко к ±1)
    if abs(nx) > 0.7:
        # Стена параллельна оси Y
        start_x = wall['x_min'] if nx > 0 else wall['x_max']
        end_x = wall['x_min'] if nx > 0 else wall['x_max']
        start_y = wall['y_min']
        end_y = wall['y_max']
    
    # Если нормаль направлена вдоль Y (ny близко к ±1)
    elif abs(ny) > 0.7:
        # Стена параллельна оси X
        start_x = wall['x_min']
        end_x = wall['x_max']
        start_y = wall['y_min'] if ny > 0 else wall['y_max']
        end_y = wall['y_min'] if ny > 0 else wall['y_max']
    
    else:
        # Диагональная стена (упрощённо)
        start_x = wall['x_min']
        start_y = wall['y_min']
        end_x = wall['x_max']
        end_y = wall['y_max']
    
    # Нормализуем координаты
    start_x, start_y = normalize_coordinates(start_x, start_y)
    end_x, end_y = normalize_coordinates(end_x, end_y)
    
    # Высота стены
    height = int(wall['height'])
    
    # Уровень (пока фиксированный)
    level = "1 этаж"
    
    return {
        "command": "CreateWall",
        "startX": start_x,
        "startY": start_y,
        "endX": end_x,
        "endY": end_y,
        "height": height,
        "thickness": wall_thickness,
        "level": level,
        "wallId": wall['id']
    }

def main():
    print("=== ЭКСПОРТ В REVIT ===\n")
    
    # Загружаем стены
    with open(INPUT_FILE) as f:
        data = json.load(f)
    
    walls = data['walls']
    
    # Фильтруем: высота > 2000мм
    valid_walls = [w for w in walls if w['height'] > 2000]
    
    print(f"Всего стен: {len(walls)}")
    print(f"Валидных стен (высота > 2м): {len(valid_walls)}\n")
    
    # Генерируем команды
    commands = []
    
    for wall in valid_walls:
        cmd = generate_wall_command(wall)
        commands.append(cmd)
    
    # Сохраняем локально
    with open(OUTPUT_LOCAL, 'w', encoding='utf-8') as f:
        for cmd in commands:
            f.write(json.dumps(cmd, ensure_ascii=False) + '\n')
    
    print(f"Сохранено локально: {OUTPUT_LOCAL}")
    print(f"Команд: {len(commands)}\n")
    
    # Показываем первые 5 команд
    print("=== ПЕРВЫЕ 5 КОМАНД ===\n")
    for cmd in commands[:5]:
        print(json.dumps(cmd, indent=2, ensure_ascii=False))
        print()
    
    print(f"\n=== ИТОГО ===")
    print(f"Стен для Revit: {len(commands)}")
    print(f"Файл готов для копирования в Windows: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
