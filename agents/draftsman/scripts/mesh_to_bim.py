#!/usr/bin/env python3
"""
Конвертер 3D Mesh (3ds Max) → BIM (Revit).
Распознаёт стены, перекрытия, окна, двери из mesh-геометрии.
"""
import requests
import json
import math
from collections import defaultdict

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '0f9e9c5ff1c0ec1e1d5241208549b264'

def fetch_object(object_id):
    """Загружает объект из Speckle"""
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{object_id}'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    return data[0] if isinstance(data, list) else data

def parse_vertices(vertices_ref_id):
    """Парсит вершины в список [(x,y,z), ...]"""
    data = fetch_object(vertices_ref_id)
    if not data or 'data' not in data:
        return []
    
    coords = data['data']
    vertices = []
    for i in range(0, len(coords) - 2, 3):
        vertices.append((coords[i], coords[i+1], coords[i+2]))
    
    return vertices

def parse_faces(faces_ref_id):
    """Парсит грани в список [[v1, v2, v3, v4], ...]"""
    data = fetch_object(faces_ref_id)
    if not data or 'data' not in data:
        return []
    
    indices = data['data']
    faces = []
    i = 0
    while i < len(indices):
        n = indices[i]
        face_vertices = indices[i+1:i+1+n]
        faces.append(face_vertices)
        i += n + 1
    
    return faces

def compute_face_normal(vertices, face):
    """Вычисляет нормаль грани (cross product)"""
    if len(face) < 3:
        return None
    
    v0 = vertices[face[0]]
    v1 = vertices[face[1]]
    v2 = vertices[face[2]]
    
    # Векторы рёбер
    edge1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
    edge2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
    
    # Cross product
    nx = edge1[1] * edge2[2] - edge1[2] * edge2[1]
    ny = edge1[2] * edge2[0] - edge1[0] * edge2[2]
    nz = edge1[0] * edge2[1] - edge1[1] * edge2[0]
    
    # Нормализация
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length == 0:
        return None
    
    return (nx/length, ny/length, nz/length)

def analyze_mesh(mesh_obj):
    """Анализирует один mesh и распознаёт элементы"""
    vertices_ref = mesh_obj['vertices'][0]['referencedId']
    faces_ref = mesh_obj['faces'][0]['referencedId']
    
    vertices = parse_vertices(vertices_ref)
    faces = parse_faces(faces_ref)
    
    print(f"\nМеш: {len(vertices)} вершин, {len(faces)} граней")
    
    walls = []
    floors = []
    ceilings = []
    
    # Находим диапазон высот
    z_values = [v[2] for v in vertices]
    z_min, z_max = min(z_values), max(z_values)
    z_threshold_floor = z_min + 100  # 100мм от низа
    z_threshold_ceil = z_max - 100    # 100мм от верха
    
    print(f"Высоты: {z_min:.1f} - {z_max:.1f} мм")
    
    for face in faces:
        if len(face) < 3:
            continue
        
        # Проверка валидности индексов
        if any(vi >= len(vertices) for vi in face):
            continue
        
        normal = compute_face_normal(vertices, face)
        if not normal:
            continue
        
        # Средняя Z координата грани
        face_z = sum(vertices[vi][2] for vi in face) / len(face)
        
        # Вычисляем реальную 3D-площадь через длину рёбер
        # Для простоты берём расстояние между крайними вершинами
        face_verts = [vertices[vi] for vi in face]
        
        # Минимум и максимум по каждой оси
        x_min = min(v[0] for v in face_verts)
        x_max = max(v[0] for v in face_verts)
        y_min = min(v[1] for v in face_verts)
        y_max = max(v[1] for v in face_verts)
        z_min = min(v[2] for v in face_verts)
        z_max = max(v[2] for v in face_verts)
        
        # Габариты грани
        width = math.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
        height = z_max - z_min
        
        # Приблизительная площадь
        area = width * height if height > 0 else width * (y_max - y_min)
        
        # Классификация
        if abs(normal[2]) < 0.5:  # Вертикальная грань (стена)
            if height > 500 and width > 300:  # Минимум 0.5м высота, 0.3м ширина
                walls.append({
                    'face': face,
                    'normal': normal,
                    'z_avg': face_z,
                    'area': area,
                    'width': width,
                    'height': height
                })
        
        elif normal[2] > 0.7 and face_z < z_threshold_floor:  # Пол
            floors.append({
                'face': face,
                'z': face_z,
                'area': area
            })
        
        elif normal[2] < -0.7 and face_z > z_threshold_ceil:  # Потолок
            ceilings.append({
                'face': face,
                'z': face_z,
                'area': area
            })
    
    print(f"Распознано: {len(walls)} стеновых граней, {len(floors)} полов, {len(ceilings)} потолков")
    
    return {
        'vertices': vertices,
        'walls': walls,
        'floors': floors,
        'ceilings': ceilings,
        'z_min': z_min,
        'z_max': z_max
    }

def main():
    print("=== АНАЛИЗ 3D MESH → BIM ===\n")
    
    # Загружаем корень
    root = fetch_object(ROOT_OBJECT_ID)
    layer_id = root['elements'][0]['referencedId']
    
    # Загружаем слой
    layer = fetch_object(layer_id)
    mesh_ids = [elem['referencedId'] for elem in layer['elements']]
    
    print(f"Файл: {root['name']}")
    print(f"Слой: {layer['name']}")
    print(f"Mesh-объектов: {len(mesh_ids)}")
    
    all_results = []
    
    # Анализируем каждый mesh
    for i, mesh_id in enumerate(mesh_ids):
        print(f"\n[{i+1}/{len(mesh_ids)}] Загружаю mesh {mesh_id[:16]}...")
        mesh = fetch_object(mesh_id)
        
        if not mesh:
            print("  Ошибка загрузки")
            continue
        
        result = analyze_mesh(mesh)
        all_results.append(result)
    
    # Статистика
    total_walls = sum(len(r['walls']) for r in all_results)
    total_floors = sum(len(r['floors']) for r in all_results)
    total_ceilings = sum(len(r['ceilings']) for r in all_results)
    
    print(f"\n=== ИТОГО ===")
    print(f"Всего стеновых граней: {total_walls}")
    print(f"Всего полов: {total_floors}")
    print(f"Всего потолков: {total_ceilings}")
    
    # Сохраняем результат
    output_path = '/home/axis/openclaw/agents/draftsman/temp/mesh_analysis.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'file': root['name'],
            'meshes': len(mesh_ids),
            'total_walls': total_walls,
            'total_floors': total_floors,
            'total_ceilings': total_ceilings
        }, f, indent=2)
    
    print(f"\nРезультат сохранён: {output_path}")

if __name__ == "__main__":
    main()
