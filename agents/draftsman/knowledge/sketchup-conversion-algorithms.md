# АЛГОРИТМЫ КОНВЕРТАЦИИ SketchUp → Revit
# Детальная реализация для агента Draftsman

## 📐 ГЕОМЕТРИЧЕСКИЕ УТИЛИТЫ

### 1. Вычисление нормали грани

```python
import math
import numpy as np

def get_face_normal(vertices):
    """
    Вычисляет нормаль (перпендикуляр) к плоскости по 3+ вершинам.
    
    Args:
        vertices: List of [x, y, z] points
    
    Returns:
        [nx, ny, nz] normalized normal vector
    """
    if len(vertices) < 3:
        return [0, 0, 1]  # default vertical
    
    v1, v2, v3 = vertices[0], vertices[1], vertices[2]
    
    # Два ребра грани
    edge1 = np.array([v2[i] - v1[i] for i in range(3)])
    edge2 = np.array([v3[i] - v1[i] for i in range(3)])
    
    # Векторное произведение
    normal = np.cross(edge1, edge2)
    
    # Нормализация
    length = np.linalg.norm(normal)
    if length == 0:
        return [0, 0, 1]
    
    return (normal / length).tolist()


def is_vertical_face(normal, tolerance_deg=10):
    """
    Проверяет вертикальность грани (нормаль горизонтальна).
    
    Args:
        normal: [nx, ny, nz]
        tolerance_deg: допуск в градусах
    
    Returns:
        True если грань почти вертикальна
    """
    # Угол между нормалью и горизонтальной плоскостью
    angle_rad = math.acos(abs(normal[2]))
    angle_deg = math.degrees(angle_rad)
    
    # Вертикальная грань имеет угол ~90° (нормаль горизонтальна)
    return abs(90 - angle_deg) < tolerance_deg


def is_horizontal_face(normal, tolerance_deg=10):
    """Проверяет горизонтальность (пол/потолок)."""
    angle_rad = math.acos(abs(normal[2]))
    angle_deg = math.degrees(angle_rad)
    
    # Горизонтальная грань имеет угол ~0° или 180°
    return angle_deg < tolerance_deg or angle_deg > (180 - tolerance_deg)
```

### 2. Bounding Box (габаритный контейнер)

```python
def get_bounding_box(vertices):
    """
    Вычисляет AABB (Axis-Aligned Bounding Box).
    
    Args:
        vertices: List of [x, y, z]
    
    Returns:
        {
            'min_x': float, 'max_x': float,
            'min_y': float, 'max_y': float,
            'min_z': float, 'max_z': float,
            'width': float,  # max_x - min_x
            'depth': float,  # max_y - min_y
            'height': float  # max_z - min_z
        }
    """
    if not vertices:
        return None
    
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    
    return {
        'min_x': min_x, 'max_x': max_x,
        'min_y': min_y, 'max_y': max_y,
        'min_z': min_z, 'max_z': max_z,
        'width': max_x - min_x,
        'depth': max_y - min_y,
        'height': max_z - min_z,
        'center': [(min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2]
    }
```

### 3. Извлечение линии стены

```python
def extract_wall_line(wall_vertices):
    """
    Извлекает нижнюю линию стены (start, end) из вершин грани.
    
    Args:
        wall_vertices: List of [x, y, z] (обычно 4 точки)
    
    Returns:
        {
            'start': [x, y, z],
            'end': [x, y, z],
            'length': float,
            'direction': [dx, dy, dz]
        }
    """
    # Найти две нижние точки (min Z)
    sorted_by_z = sorted(wall_vertices, key=lambda v: v[2])
    bottom_points = sorted_by_z[:2]
    
    # Сортировать по X (или Y если X одинаков)
    if abs(bottom_points[0][0] - bottom_points[1][0]) > 0.01:
        bottom_points.sort(key=lambda v: v[0])
    else:
        bottom_points.sort(key=lambda v: v[1])
    
    start, end = bottom_points
    
    # Направление
    direction = [end[i] - start[i] for i in range(3)]
    length = math.sqrt(sum(d*d for d in direction))
    
    # Нормализация направления
    if length > 0:
        direction = [d / length for d in direction]
    
    return {
        'start': start,
        'end': end,
        'length': length,
        'direction': direction
    }
```

---

## 🧱 РАСПОЗНАВАНИЕ СТЕН

```python
def classify_wall(face_data):
    """
    Классифицирует грань как стену.
    
    Args:
        face_data: {
            'vertices': [[x,y,z], ...],
            'normal': [nx, ny, nz],
            'area': float
        }
    
    Returns:
        {
            'is_wall': bool,
            'confidence': float,  # 0.0-1.0
            'reason': str,
            'wall_data': {...} if is_wall else None
        }
    """
    vertices = face_data['vertices']
    normal = face_data.get('normal') or get_face_normal(vertices)
    
    bbox = get_bounding_box(vertices)
    
    # Критерий 1: Вертикальность
    is_vertical = is_vertical_face(normal, tolerance_deg=15)
    if not is_vertical:
        return {
            'is_wall': False,
            'confidence': 0.0,
            'reason': 'Not vertical'
        }
    
    # Критерий 2: Высота
    MIN_WALL_HEIGHT = 2.0  # 2 метра
    height = bbox['height']
    if height < MIN_WALL_HEIGHT:
        return {
            'is_wall': False,
            'confidence': 0.2,
            'reason': f'Too short: {height:.2f}m < {MIN_WALL_HEIGHT}m'
        }
    
    # Критерий 3: Толщина (если есть)
    # В SketchUp стены часто представлены как грань без толщины
    # Толщина определяется на этапе генерации JSONL
    
    # Критерий 4: Длина
    MIN_WALL_LENGTH = 0.3  # 30 см
    wall_line = extract_wall_line(vertices)
    length = wall_line['length']
    if length < MIN_WALL_LENGTH:
        return {
            'is_wall': False,
            'confidence': 0.3,
            'reason': f'Too short: {length:.2f}m'
        }
    
    # Вычисление уверенности
    confidence = 1.0
    if height < 2.5:
        confidence -= (2.5 - height) * 0.1
    if not is_vertical_face(normal, tolerance_deg=5):
        confidence -= 0.1
    
    wall_data = {
        'start': wall_line['start'],
        'end': wall_line['end'],
        'height': height,
        'length': length,
        'thickness': 0.2,  # default 200мм, можно настроить
        'normal': normal,
        'bbox': bbox
    }
    
    return {
        'is_wall': True,
        'confidence': max(0.5, confidence),
        'reason': 'Valid wall geometry',
        'wall_data': wall_data
    }
```

---

## 🚪 РАСПОЗНАВАНИЕ ПРОЁМОВ (ДВЕРИ И ОКНА)

```python
def find_openings_in_wall(wall_data, all_faces):
    """
    Находит проёмы (двери/окна) внутри стены.
    
    Args:
        wall_data: результат classify_wall()
        all_faces: список всех граней модели
    
    Returns:
        [
            {
                'type': 'door' | 'window',
                'bbox': {...},
                'location': [x, y, z],
                'width': float,
                'height': float
            },
            ...
        ]
    """
    openings = []
    
    # Плоскость стены
    wall_normal = wall_data['normal']
    wall_start = wall_data['start']
    
    # Уравнение плоскости: Ax + By + Cz + D = 0
    # где (A, B, C) = normal, D = -(normal · point)
    D = -(wall_normal[0]*wall_start[0] + 
          wall_normal[1]*wall_start[1] + 
          wall_normal[2]*wall_start[2])
    
    wall_plane = {
        'normal': wall_normal,
        'D': D
    }
    
    for face in all_faces:
        vertices = face.get('vertices', [])
        if len(vertices) < 3:
            continue
        
        # Проверить копланарность (грань в той же плоскости)
        if not is_coplanar_to_wall(vertices, wall_plane, tolerance=0.05):
            continue
        
        # Проверить что грань внутри контура стены
        bbox = get_bounding_box(vertices)
        if not is_inside_wall_bounds(bbox, wall_data):
            continue
        
        # Классифицировать проём
        opening = classify_opening(bbox, wall_data)
        if opening:
            openings.append(opening)
    
    return openings


def is_coplanar_to_wall(vertices, wall_plane, tolerance=0.05):
    """Проверяет что вершины лежат в плоскости стены."""
    A, B, C = wall_plane['normal']
    D = wall_plane['D']
    
    for v in vertices:
        # Расстояние точки до плоскости
        dist = abs(A*v[0] + B*v[1] + C*v[2] + D)
        if dist > tolerance:
            return False
    
    return True


def is_inside_wall_bounds(opening_bbox, wall_data):
    """Проверяет что проём внутри габаритов стены."""
    wall_bbox = wall_data['bbox']
    
    # Проверка по X, Y, Z
    in_x = (wall_bbox['min_x'] <= opening_bbox['min_x'] and 
            opening_bbox['max_x'] <= wall_bbox['max_x'])
    in_y = (wall_bbox['min_y'] <= opening_bbox['min_y'] and 
            opening_bbox['max_y'] <= wall_bbox['max_y'])
    in_z = (wall_bbox['min_z'] <= opening_bbox['min_z'] and 
            opening_bbox['max_z'] <= wall_bbox['max_z'])
    
    # Достаточно попадания по 2 из 3 осей (стена может быть наклонной)
    return sum([in_x, in_y, in_z]) >= 2


def classify_opening(bbox, wall_data):
    """
    Определяет тип проёма: дверь или окно.
    
    Критерии:
    - Дверь: 0.7-1.2м ширина, 2.0-2.4м высота, низ на полу (z ≈ 0)
    - Окно: 0.5-2.0м ширина, 1.0-1.8м высота, низ выше пола (z > 0.8м)
    """
    width = bbox['width']
    height = bbox['height']
    bottom_z = bbox['min_z']
    
    # Параметры дверей
    DOOR_WIDTH_MIN = 0.7
    DOOR_WIDTH_MAX = 1.2
    DOOR_HEIGHT_MIN = 2.0
    DOOR_HEIGHT_MAX = 2.5
    DOOR_SILL_MAX = 0.2  # порог максимум 20 см
    
    # Параметры окон
    WINDOW_WIDTH_MIN = 0.5
    WINDOW_WIDTH_MAX = 2.5
    WINDOW_HEIGHT_MIN = 0.8
    WINDOW_HEIGHT_MAX = 2.0
    WINDOW_SILL_MIN = 0.7  # подоконник минимум 70 см
    
    # Проверка на дверь
    is_door_size = (DOOR_WIDTH_MIN <= width <= DOOR_WIDTH_MAX and 
                    DOOR_HEIGHT_MIN <= height <= DOOR_HEIGHT_MAX)
    is_door_position = bottom_z <= DOOR_SILL_MAX
    
    if is_door_size and is_door_position:
        return {
            'type': 'door',
            'bbox': bbox,
            'location': bbox['center'],
            'width': width,
            'height': height,
            'sill_height': bottom_z
        }
    
    # Проверка на окно
    is_window_size = (WINDOW_WIDTH_MIN <= width <= WINDOW_WIDTH_MAX and 
                      WINDOW_HEIGHT_MIN <= height <= WINDOW_HEIGHT_MAX)
    is_window_position = bottom_z >= WINDOW_SILL_MIN
    
    if is_window_size and is_window_position:
        return {
            'type': 'window',
            'bbox': bbox,
            'location': bbox['center'],
            'width': width,
            'height': height,
            'sill_height': bottom_z
        }
    
    # Не подходит под критерии
    return None
```

---

## 🏠 РАСПОЗНАВАНИЕ ПОМЕЩЕНИЙ

```python
def extract_rooms_from_groups(root):
    """
    Извлекает помещения из SketchUp групп/компонентов.
    
    Args:
        root: корневой объект Speckle
    
    Returns:
        [
            {
                'name': str,
                'area': float,
                'perimeter': float,
                'boundary': [[x,y], ...],  # контур на плоскости
                'height': float,
                'level': str
            },
            ...
        ]
    """
    rooms = []
    
    # Найти все группы
    groups = find_groups(root)
    
    for group in groups:
        # Извлечь стены и пол группы
        walls = []
        floor = None
        
        for element in group.get('elements', []):
            if hasattr(element, 'vertices'):
                normal = get_face_normal(element.vertices)
                
                if is_vertical_face(normal):
                    walls.append(element)
                elif is_horizontal_face(normal):
                    bbox = get_bounding_box(element.vertices)
                    # Выбрать нижнюю горизонтальную плоскость (пол)
                    if floor is None or bbox['min_z'] < get_bounding_box(floor.vertices)['min_z']:
                        floor = element
        
        # Проверить что найдены и стены и пол
        if not walls or not floor:
            continue
        
        # Вычислить контур помещения (проекция на плоскость XY)
        floor_vertices = floor.vertices
        boundary_2d = [[v[0], v[1]] for v in floor_vertices]
        
        # Вычислить площадь (формула Shoelace)
        area = calculate_polygon_area(boundary_2d)
        
        # Вычислить высоту (от пола до потолка)
        floor_z = min(v[2] for v in floor_vertices)
        ceiling_z = max(max(v[2] for v in wall.vertices) for wall in walls)
        height = ceiling_z - floor_z
        
        rooms.append({
            'name': group.get('name', f'Room_{len(rooms)+1}'),
            'area': area,
            'perimeter': calculate_perimeter(boundary_2d),
            'boundary': boundary_2d,
            'height': height,
            'level': '1 этаж',  # TODO: определять уровень по Z
            'floor_elevation': floor_z
        })
    
    return rooms


def calculate_polygon_area(vertices_2d):
    """Площадь полигона по формуле Shoelace."""
    n = len(vertices_2d)
    if n < 3:
        return 0.0
    
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += vertices_2d[i][0] * vertices_2d[j][1]
        area -= vertices_2d[j][0] * vertices_2d[i][1]
    
    return abs(area) / 2.0


def calculate_perimeter(vertices_2d):
    """Периметр полигона."""
    n = len(vertices_2d)
    if n < 2:
        return 0.0
    
    perimeter = 0.0
    for i in range(n):
        j = (i + 1) % n
        dx = vertices_2d[j][0] - vertices_2d[i][0]
        dy = vertices_2d[j][1] - vertices_2d[i][1]
        perimeter += math.sqrt(dx*dx + dy*dy)
    
    return perimeter
```

---

## 📄 ГЕНЕРАЦИЯ JSONL

```python
import json

def to_revit_mm(meters):
    """Конвертация метров в миллиметры (целые)."""
    return int(round(meters * 1000))


def generate_jsonl_commands(walls, doors, windows, rooms, output_path):
    """
    Генерирует JSONL файл для pyRevit Bridge.
    
    Args:
        walls: list of wall_data
        doors: list of door_data
        windows: list of window_data
        rooms: list of room_data
        output_path: path to output .jsonl file
    
    Returns:
        int: количество команд
    """
    commands = []
    
    # 1. Создать уровень
    commands.append({
        "command": "CreateLevel",
        "name": "1 этаж",
        "elevation": 0
    })
    
    # 2. Стены
    wall_ids = {}
    for i, wall in enumerate(walls):
        wall_id = f"wall_{i}"
        wall_ids[id(wall)] = wall_id
        
        commands.append({
            "command": "CreateWall",
            "id": wall_id,
            "startX": to_revit_mm(wall['start'][0]),
            "startY": to_revit_mm(wall['start'][1]),
            "endX": to_revit_mm(wall['end'][0]),
            "endY": to_revit_mm(wall['end'][1]),
            "height": to_revit_mm(wall['height']),
            "thickness": to_revit_mm(wall.get('thickness', 0.2)),
            "level": "1 этаж"
        })
    
    # 3. Двери
    for door in doors:
        # Найти ближайшую стену
        wall_id = find_closest_wall(door, walls, wall_ids)
        
        commands.append({
            "command": "CreateDoor",
            "wallId": wall_id,
            "locationX": to_revit_mm(door['location'][0]),
            "locationY": to_revit_mm(door['location'][1]),
            "width": to_revit_mm(door['width']),
            "height": to_revit_mm(door['height']),
            "level": "1 этаж"
        })
    
    # 4. Окна
    for window in windows:
        wall_id = find_closest_wall(window, walls, wall_ids)
        
        commands.append({
            "command": "CreateWindow",
            "wallId": wall_id,
            "locationX": to_revit_mm(window['location'][0]),
            "locationY": to_revit_mm(window['location'][1]),
            "sillHeight": to_revit_mm(window['sill_height']),
            "width": to_revit_mm(window['width']),
            "height": to_revit_mm(window['height']),
            "level": "1 этаж"
        })
    
    # 5. Помещения
    for room in rooms:
        # Конвертировать контур
        boundary_mm = [[to_revit_mm(p[0]), to_revit_mm(p[1])] for p in room['boundary']]
        
        commands.append({
            "command": "CreateRoom",
            "name": room['name'],
            "boundaryPoints": boundary_mm,
            "level": "1 этаж"
        })
    
    # Записать в файл
    with open(output_path, 'w', encoding='utf-8') as f:
        for cmd in commands:
            f.write(json.dumps(cmd, ensure_ascii=False) + '\n')
    
    return len(commands)


def find_closest_wall(opening, walls, wall_ids):
    """Находит стену, ближайшую к проёму."""
    min_dist = float('inf')
    closest_wall = None
    
    opening_center = opening['location']
    
    for wall in walls:
        # Расстояние от точки до отрезка (линия стены)
        dist = point_to_segment_distance(opening_center, wall['start'], wall['end'])
        
        if dist < min_dist:
            min_dist = dist
            closest_wall = wall
    
    return wall_ids[id(closest_wall)] if closest_wall else "wall_0"


def point_to_segment_distance(point, seg_start, seg_end):
    """Расстояние от точки до отрезка в 3D."""
    # Вектор отрезка
    dx = seg_end[0] - seg_start[0]
    dy = seg_end[1] - seg_start[1]
    dz = seg_end[2] - seg_start[2]
    
    # Длина отрезка
    seg_len_sq = dx*dx + dy*dy + dz*dz
    if seg_len_sq == 0:
        # Отрезок вырожден в точку
        return math.sqrt(
            (point[0] - seg_start[0])**2 +
            (point[1] - seg_start[1])**2 +
            (point[2] - seg_start[2])**2
        )
    
    # Параметр проекции (0 = start, 1 = end)
    t = max(0, min(1, (
        (point[0] - seg_start[0]) * dx +
        (point[1] - seg_start[1]) * dy +
        (point[2] - seg_start[2]) * dz
    ) / seg_len_sq))
    
    # Ближайшая точка на отрезке
    proj_x = seg_start[0] + t * dx
    proj_y = seg_start[1] + t * dy
    proj_z = seg_start[2] + t * dz
    
    # Расстояние
    return math.sqrt(
        (point[0] - proj_x)**2 +
        (point[1] - proj_y)**2 +
        (point[2] - proj_z)**2
    )
```

---

## 🎯 ИТОГОВЫЙ АЛГОРИТМ

```python
def full_conversion_pipeline(project_id, output_path="/mnt/c/bridge/revit_commands.jsonl"):
    """
    Полный цикл конвертации SketchUp → Revit.
    
    Returns:
        {
            'status': 'success' | 'error',
            'elements': {...},
            'output_file': str,
            'command_count': int
        }
    """
    try:
        # 1. Подключение
        client = authenticate_speckle()
        root = get_latest_model(client, project_id)
        
        # 2. Извлечение геометрии
        all_faces = extract_all_faces(root)
        
        # 3. Распознавание стен
        walls = []
        for face in all_faces:
            result = classify_wall(face)
            if result['is_wall'] and result['confidence'] > 0.7:
                walls.append(result['wall_data'])
        
        # 4. Поиск проёмов
        doors = []
        windows = []
        for wall in walls:
            openings = find_openings_in_wall(wall, all_faces)
            for opening in openings:
                if opening['type'] == 'door':
                    doors.append(opening)
                else:
                    windows.append(opening)
        
        # 5. Распознавание помещений
        rooms = extract_rooms_from_groups(root)
        
        # 6. Генерация JSONL
        command_count = generate_jsonl_commands(walls, doors, windows, rooms, output_path)
        
        return {
            'status': 'success',
            'elements': {
                'walls': len(walls),
                'doors': len(doors),
                'windows': len(windows),
                'rooms': len(rooms)
            },
            'output_file': output_path,
            'command_count': command_count
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
```
