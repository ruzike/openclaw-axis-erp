import json

commands = []

# 1. Уровни (Levels) - 3 этажа
commands.append({"command": "level", "name": "Level 1", "elevation_mm": 0})
commands.append({"command": "level", "name": "Level 2", "elevation_mm": 3000})
commands.append({"command": "level", "name": "Level 3", "elevation_mm": 6000})

# 2. Оси (Grids)
# Вертикальные оси (1, 2)
commands.append({"command": "grid", "name": "1", "x1_mm": 0, "y1_mm": -2000, "x2_mm": 0, "y2_mm": 12000})
commands.append({"command": "grid", "name": "2", "x1_mm": 10000, "y1_mm": -2000, "x2_mm": 10000, "y2_mm": 12000})
# Горизонтальные оси (A, B)
commands.append({"command": "grid", "name": "A", "x1_mm": -2000, "y1_mm": 0, "x2_mm": 16000, "y2_mm": 0})
commands.append({"command": "grid", "name": "B", "x1_mm": -2000, "y1_mm": 10000, "x2_mm": 12000, "y2_mm": 10000})

# 3. Стены (Walls)
# Основной дом 10х10 (3 этажа)
for level in ["Level 1", "Level 2", "Level 3"]:
    # Южная стена
    commands.append({"command": "wall", "x1_mm": 0, "y1_mm": 0, "x2_mm": 10000, "y2_mm": 0, "thickness_mm": 400, "height_mm": 3000, "type": "exterior", "level": level})
    # Восточная стена
    commands.append({"command": "wall", "x1_mm": 10000, "y1_mm": 0, "x2_mm": 10000, "y2_mm": 10000, "thickness_mm": 400, "height_mm": 3000, "type": "exterior", "level": level})
    # Северная стена
    commands.append({"command": "wall", "x1_mm": 10000, "y1_mm": 10000, "x2_mm": 0, "y2_mm": 10000, "thickness_mm": 400, "height_mm": 3000, "type": "exterior", "level": level})
    # Западная стена
    commands.append({"command": "wall", "x1_mm": 0, "y1_mm": 10000, "x2_mm": 0, "y2_mm": 0, "thickness_mm": 400, "height_mm": 3000, "type": "exterior", "level": level})

# Гараж (пристройка справа к Level 1: 4х6 м)
# Южная стена гаража
commands.append({"command": "wall", "x1_mm": 10000, "y1_mm": 2000, "x2_mm": 14000, "y2_mm": 2000, "thickness_mm": 300, "height_mm": 3000, "type": "exterior", "level": "Level 1"})
# Восточная стена гаража
commands.append({"command": "wall", "x1_mm": 14000, "y1_mm": 2000, "x2_mm": 14000, "y2_mm": 8000, "thickness_mm": 300, "height_mm": 3000, "type": "exterior", "level": "Level 1"})
# Северная стена гаража
commands.append({"command": "wall", "x1_mm": 14000, "y1_mm": 8000, "x2_mm": 10000, "y2_mm": 8000, "thickness_mm": 300, "height_mm": 3000, "type": "exterior", "level": "Level 1"})

# 4. Двери (Doors)
# Главный вход (Level 1, по центру южной стены)
commands.append({"command": "door", "x_mm": 5000, "y_mm": 0, "width_mm": 1000, "height_mm": 2100, "level": "Level 1", "family": ""})
# Ворота гаража (широкая дверь на южной стене гаража)
commands.append({"command": "door", "x_mm": 12000, "y_mm": 2000, "width_mm": 2500, "height_mm": 2400, "level": "Level 1", "family": ""})
# Дверь из дома в гараж (на восточной стене основного дома)
commands.append({"command": "door", "x_mm": 10000, "y_mm": 5000, "width_mm": 900, "height_mm": 2100, "level": "Level 1", "family": ""})
# Дверь на балкон (Level 2)
commands.append({"command": "door", "x_mm": 5000, "y_mm": 0, "width_mm": 900, "height_mm": 2100, "level": "Level 2", "family": ""})

# 5. Окна (Windows)
window_w = 1500
window_h = 1600
window_sill = 900

for level in ["Level 1", "Level 2", "Level 3"]:
    # Окна на южном фасаде
    commands.append({"command": "window", "x_mm": 2000, "y_mm": 0, "width_mm": window_w, "height_mm": window_h, "sill_mm": window_sill, "level": level, "family": ""})
    commands.append({"command": "window", "x_mm": 8000, "y_mm": 0, "width_mm": window_w, "height_mm": window_h, "sill_mm": window_sill, "level": level, "family": ""})
    if level == "Level 3": # На 3 этаже по центру окно вместо двери
        commands.append({"command": "window", "x_mm": 5000, "y_mm": 0, "width_mm": window_w, "height_mm": window_h, "sill_mm": window_sill, "level": level, "family": ""})

    # Окна на северном фасаде (сзади)
    commands.append({"command": "window", "x_mm": 3000, "y_mm": 10000, "width_mm": window_w, "height_mm": window_h, "sill_mm": window_sill, "level": level, "family": ""})
    commands.append({"command": "window", "x_mm": 7000, "y_mm": 10000, "width_mm": window_w, "height_mm": window_h, "sill_mm": window_sill, "level": level, "family": ""})

    # Окна на западном фасаде (слева)
    commands.append({"command": "window", "x_mm": 0, "y_mm": 3000, "width_mm": window_w, "height_mm": window_h, "sill_mm": window_sill, "level": level, "family": ""})
    commands.append({"command": "window", "x_mm": 0, "y_mm": 7000, "width_mm": window_w, "height_mm": window_h, "sill_mm": window_sill, "level": level, "family": ""})

# Окно в гараже
commands.append({"command": "window", "x_mm": 14000, "y_mm": 5000, "width_mm": 1200, "height_mm": 800, "sill_mm": 1500, "level": "Level 1", "family": ""})

# Запись в файл
with open('/mnt/c/bridge/revit_commands.jsonl', 'w') as f:
    for cmd in commands:
        f.write(json.dumps(cmd) + '\n')

print("✅ Commands generated to /mnt/c/bridge/revit_commands.jsonl")
