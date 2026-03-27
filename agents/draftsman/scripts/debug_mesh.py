#!/usr/bin/env python3
"""
Отладка mesh: показывает нормали первых 20 граней.
"""
import requests
import math

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'

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

def main():
    # Берём первый большой mesh (05e5109297fcc805...)
    mesh_id = '05e5109297fcc805900942d24df83376'
    
    print("=== ОТЛАДКА MESH ===\n")
    print(f"ID: {mesh_id}\n")
    
    mesh = fetch_object(mesh_id)
    vertices_ref = mesh['vertices'][0]['referencedId']
    faces_ref = mesh['faces'][0]['referencedId']
    
    vertices = parse_vertices(vertices_ref)
    faces = parse_faces(faces_ref)
    
    print(f"Вершин: {len(vertices)}")
    print(f"Граней: {len(faces)}\n")
    
    print("=== НОРМАЛИ ПЕРВЫХ 20 ГРАНЕЙ ===\n")
    
    for i, face in enumerate(faces[:20]):
        normal = compute_face_normal(vertices, face)
        if not normal:
            print(f"Грань {i}: невалидная")
            continue
        
        # Площадь
        area = abs(sum(
            (vertices[face[j]][0] - vertices[face[j-1]][0]) *
            (vertices[face[j]][1] + vertices[face[j-1]][1])
            for j in range(len(face))
        ) / 2)
        
        # Средняя Z
        z_avg = sum(vertices[vi][2] for vi in face) / len(face)
        
        # Классификация
        classification = "?"
        if abs(normal[2]) < 0.5:
            classification = "СТЕНА (вертикальная)"
        elif normal[2] > 0.7:
            classification = "ПОЛ (вверх)"
        elif normal[2] < -0.7:
            classification = "ПОТОЛОК (вниз)"
        
        print(f"Грань {i}:")
        print(f"  Нормаль: ({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f})")
        print(f"  Площадь: {area/1_000_000:.4f} м²")
        print(f"  Z средняя: {z_avg:.1f} мм")
        print(f"  Классификация: {classification}")
        print()

if __name__ == "__main__":
    main()
