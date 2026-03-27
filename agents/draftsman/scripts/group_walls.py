#!/usr/bin/env python3
"""
Группировка граней mesh в логические стены.
Алгоритм: объединяем грани с похожей нормалью и близким расположением.
"""
import requests
import json
import math
from collections import defaultdict

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '0f9e9c5ff1c0ec1e1d5241208549b264'

def fetch_object(object_id):
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
    data = fetch_object(vertices_ref_id)
    if not data or 'data' not in data:
        return []
    
    coords = data['data']
    vertices = []
    for i in range(0, len(coords) - 2, 3):
        vertices.append((coords[i], coords[i+1], coords[i+2]))
    
    return vertices

def parse_faces(faces_ref_id):
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
    if len(face) < 3:
        return None
    
    if any(vi >= len(vertices) for vi in face):
        return None
    
    v0 = vertices[face[0]]
    v1 = vertices[face[1]]
    v2 = vertices[face[2]]
    
    edge1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
    edge2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
    
    nx = edge1[1] * edge2[2] - edge1[2] * edge2[1]
    ny = edge1[2] * edge2[0] - edge1[0] * edge2[2]
    nz = edge1[0] * edge2[1] - edge1[1] * edge2[0]
    
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length == 0:
        return None
    
    return (nx/length, ny/length, nz/length)

def get_face_bounds(vertices, face):
    """Возвращает габариты грани"""
    face_verts = [vertices[vi] for vi in face]
    
    x_vals = [v[0] for v in face_verts]
    y_vals = [v[1] for v in face_verts]
    z_vals = [v[2] for v in face_verts]
    
    return {
        'x_min': min(x_vals),
        'x_max': max(x_vals),
        'y_min': min(y_vals),
        'y_max': max(y_vals),
        'z_min': min(z_vals),
        'z_max': max(z_vals),
        'center': (
            (min(x_vals) + max(x_vals)) / 2,
            (min(y_vals) + max(y_vals)) / 2,
            (min(z_vals) + max(z_vals)) / 2
        )
    }

def normals_similar(n1, n2, threshold=0.95):
    """Проверяет, похожи ли нормали (cos угла > threshold)"""
    dot = n1[0]*n2[0] + n1[1]*n2[1] + n1[2]*n2[2]
    return dot > threshold

def faces_adjacent(bounds1, bounds2, tolerance=500):
    """Проверяет, близки ли грани (расстояние < tolerance мм)"""
    c1 = bounds1['center']
    c2 = bounds2['center']
    
    dist = math.sqrt(
        (c1[0] - c2[0])**2 +
        (c1[1] - c2[1])**2 +
        (c1[2] - c2[2])**2
    )
    
    return dist < tolerance

def group_wall_faces(wall_faces, vertices):
    """Группирует грани в логические стены"""
    groups = []
    used = set()
    
    for i, face_data in enumerate(wall_faces):
        if i in used:
            continue
        
        # Начинаем новую группу
        group = [i]
        used.add(i)
        
        face_i = face_data['face']
        normal_i = face_data['normal']
        bounds_i = get_face_bounds(vertices, face_i)
        
        # Ищем похожие грани
        for j, other_data in enumerate(wall_faces):
            if j in used or j == i:
                continue
            
            face_j = other_data['face']
            normal_j = other_data['normal']
            bounds_j = get_face_bounds(vertices, face_j)
            
            # Проверяем похожесть нормалей
            if normals_similar(normal_i, normal_j):
                # Проверяем близость
                if faces_adjacent(bounds_i, bounds_j, tolerance=3000):
                    group.append(j)
                    used.add(j)
        
        groups.append(group)
    
    return groups

def analyze_mesh(mesh_obj, vertices):
    """Анализирует mesh и находит стеновые грани"""
    faces_ref = mesh_obj['faces'][0]['referencedId']
    faces = parse_faces(faces_ref)
    
    wall_faces = []
    
    for face in faces:
        if len(face) < 3:
            continue
        
        if any(vi >= len(vertices) for vi in face):
            continue
        
        normal = compute_face_normal(vertices, face)
        if not normal:
            continue
        
        face_verts = [vertices[vi] for vi in face]
        z_min = min(v[2] for v in face_verts)
        z_max = max(v[2] for v in face_verts)
        height = z_max - z_min
        
        x_min = min(v[0] for v in face_verts)
        x_max = max(v[0] for v in face_verts)
        y_min = min(v[1] for v in face_verts)
        y_max = max(v[1] for v in face_verts)
        width = math.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
        
        # Вертикальная грань (стена)
        if abs(normal[2]) < 0.5 and height > 500 and width > 300:
            wall_faces.append({
                'face': face,
                'normal': normal,
                'height': height,
                'width': width
            })
    
    return wall_faces

def main():
    print("=== ГРУППИРОВКА СТЕН ===\n")
    
    # Загружаем структуру
    root = fetch_object(ROOT_OBJECT_ID)
    layer_id = root['elements'][0]['referencedId']
    layer = fetch_object(layer_id)
    mesh_ids = [elem['referencedId'] for elem in layer['elements']]
    
    print(f"Файл: {root['name']}")
    print(f"Mesh-объектов: {len(mesh_ids)}\n")
    
    all_wall_faces = []
    all_vertices = []
    
    # Собираем все стеновые грани из всех mesh
    for i, mesh_id in enumerate(mesh_ids):
        print(f"[{i+1}/{len(mesh_ids)}] Загружаю mesh...")
        mesh = fetch_object(mesh_id)
        
        if not mesh:
            continue
        
        vertices_ref = mesh['vertices'][0]['referencedId']
        vertices = parse_vertices(vertices_ref)
        
        wall_faces = analyze_mesh(mesh, vertices)
        
        print(f"  Найдено стеновых граней: {len(wall_faces)}")
        
        # Сохраняем грани с привязкой к вершинам
        for face_data in wall_faces:
            all_wall_faces.append({
                'face_data': face_data,
                'vertices': vertices,
                'mesh_id': mesh_id
            })
    
    print(f"\nВсего стеновых граней: {len(all_wall_faces)}\n")
    
    # Группируем по mesh (для простоты)
    walls_by_mesh = defaultdict(list)
    for item in all_wall_faces:
        walls_by_mesh[item['mesh_id']].append(item)
    
    total_walls = 0
    wall_list = []
    
    print("=== ГРУППИРОВКА ПО MESH ===\n")
    
    for mesh_id, items in walls_by_mesh.items():
        if not items:
            continue
        
        vertices = items[0]['vertices']
        face_data_list = [item['face_data'] for item in items]
        
        groups = group_wall_faces(face_data_list, vertices)
        
        print(f"Mesh {mesh_id[:16]}:")
        print(f"  Граней: {len(items)}")
        print(f"  Стен (групп): {len(groups)}")
        
        for group_idx, group in enumerate(groups):
            # Считаем габариты группы
            all_bounds = [get_face_bounds(vertices, face_data_list[fi]['face']) 
                          for fi in group]
            
            x_min = min(b['x_min'] for b in all_bounds)
            x_max = max(b['x_max'] for b in all_bounds)
            y_min = min(b['y_min'] for b in all_bounds)
            y_max = max(b['y_max'] for b in all_bounds)
            z_min = min(b['z_min'] for b in all_bounds)
            z_max = max(b['z_max'] for b in all_bounds)
            
            length = math.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
            height = z_max - z_min
            
            # Нормаль первой грани группы
            normal = face_data_list[group[0]]['normal']
            
            wall_list.append({
                'id': f"wall_{total_walls + 1}",
                'mesh_id': mesh_id,
                'faces_count': len(group),
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max,
                'z_min': z_min,
                'z_max': z_max,
                'length': length,
                'height': height,
                'normal': normal
            })
            
            total_walls += 1
        
        print()
    
    print(f"=== ИТОГО СТЕН: {total_walls} ===\n")
    
    # Сохраняем результат
    output_path = '/home/axis/openclaw/agents/draftsman/temp/walls_grouped.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'file': root['name'],
            'total_walls': total_walls,
            'walls': wall_list
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Результат: {output_path}")
    
    # Показываем топ-10 стен
    print("\n=== ТОП-10 СТЕН ===\n")
    sorted_walls = sorted(wall_list, key=lambda w: w['length'], reverse=True)
    
    for i, wall in enumerate(sorted_walls[:10]):
        print(f"{i+1}. {wall['id']}")
        print(f"   Длина: {wall['length']/1000:.2f} м")
        print(f"   Высота: {wall['height']/1000:.2f} м")
        print(f"   Граней: {wall['faces_count']}")
        print(f"   Нормаль: ({wall['normal'][0]:.2f}, {wall['normal'][1]:.2f}, {wall['normal'][2]:.2f})")
        print()

if __name__ == "__main__":
    main()
