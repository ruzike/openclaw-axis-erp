#!/usr/bin/env python3
"""
Полная конвертация 3D Mesh → Revit JSONL (всё в одном скрипте).
"""
import requests
import json
import math
from collections import defaultdict

TOKEN_PATH = '/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt'
PROJECT_ID = '30eb4c8084'
ROOT_OBJECT_ID = '0f9e9c5ff1c0ec1e1d5241208549b264'
OUTPUT_FILE = '/home/axis/openclaw/agents/draftsman/temp/revit_commands.jsonl'

MIN_WALL_HEIGHT = 2000  # мм
WALL_THICKNESS = 200     # мм
LEVEL_NAME = "1 этаж"

def fetch(obj_id):
    with open(TOKEN_PATH) as f:
        token = f.read().strip()
    url = f'https://app.speckle.systems/objects/{PROJECT_ID}/{obj_id}'
    r = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    data = r.json()
    return data[0] if isinstance(data, list) else data

def parse_verts(ref_id):
    d = fetch(ref_id)
    if not d or 'data' not in d: return []
    c = d['data']
    return [(c[i], c[i+1], c[i+2]) for i in range(0, len(c)-2, 3)]

def parse_faces(ref_id):
    d = fetch(ref_id)
    if not d or 'data' not in d: return []
    idx = d['data']
    faces, i = [], 0
    while i < len(idx):
        n = idx[i]
        faces.append(idx[i+1:i+1+n])
        i += n + 1
    return faces

def normal(verts, face):
    if len(face) < 3 or any(vi >= len(verts) for vi in face): return None
    v0, v1, v2 = verts[face[0]], verts[face[1]], verts[face[2]]
    e1 = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2])
    e2 = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
    nx = e1[1]*e2[2] - e1[2]*e2[1]
    ny = e1[2]*e2[0] - e1[0]*e2[2]
    nz = e1[0]*e2[1] - e1[1]*e2[0]
    L = math.sqrt(nx*nx + ny*ny + nz*nz)
    return (nx/L, ny/L, nz/L) if L > 0 else None

def get_walls_from_mesh(mesh, verts):
    faces = parse_faces(mesh['faces'][0]['referencedId'])
    walls = []
    for f in faces:
        if len(f) < 3 or any(vi >= len(verts) for vi in f): continue
        n = normal(verts, f)
        if not n: continue
        fv = [verts[vi] for vi in f]
        z_min, z_max = min(v[2] for v in fv), max(v[2] for v in fv)
        h = z_max - z_min
        x_vals = [v[0] for v in fv]
        y_vals = [v[1] for v in fv]
        w = math.sqrt((max(x_vals)-min(x_vals))**2 + (max(y_vals)-min(y_vals))**2)
        if abs(n[2]) < 0.5 and h > 500 and w > 300:
            walls.append({
                'n': n,
                'h': h,
                'x': (min(x_vals), max(x_vals)),
                'y': (min(y_vals), max(y_vals))
            })
    return walls

def group_walls(walls):
    groups, used = [], set()
    for i, w1 in enumerate(walls):
        if i in used: continue
        g = [i]
        used.add(i)
        for j, w2 in enumerate(walls):
            if j in used or j == i: continue
            # Похожие нормали
            dot = sum(a*b for a,b in zip(w1['n'], w2['n']))
            if dot < 0.95: continue
            # Близкие центры
            c1 = ((w1['x'][0]+w1['x'][1])/2, (w1['y'][0]+w1['y'][1])/2)
            c2 = ((w2['x'][0]+w2['x'][1])/2, (w2['y'][0]+w2['y'][1])/2)
            dist = math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
            if dist < 3000:
                g.append(j)
                used.add(j)
        groups.append(g)
    return groups

def make_command(walls, group):
    xs = [x for i in group for x in walls[i]['x']]
    ys = [y for i in group for y in walls[i]['y']]
    hs = [walls[i]['h'] for i in group]
    n = walls[group[0]]['n']
    
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    h = int(max(hs))
    
    if abs(n[0]) > 0.7:
        sx, ex = (x_min if n[0] > 0 else x_max), (x_min if n[0] > 0 else x_max)
        sy, ey = y_min, y_max
    elif abs(n[1]) > 0.7:
        sx, ex = x_min, x_max
        sy, ey = (y_min if n[1] > 0 else y_max), (y_min if n[1] > 0 else y_max)
    else:
        sx, sy, ex, ey = x_min, y_min, x_max, y_max
    
    return {
        "command": "CreateWall",
        "startX": int(sx),
        "startY": int(sy),
        "endX": int(ex),
        "endY": int(ey),
        "height": h,
        "thickness": WALL_THICKNESS,
        "level": LEVEL_NAME
    }

print("=== 3DS MAX → REVIT ===\n")

root = fetch(ROOT_OBJECT_ID)
layer = fetch(root['elements'][0]['referencedId'])
mesh_ids = [e['referencedId'] for e in layer['elements']]

print(f"Mesh-объектов: {len(mesh_ids)}\n")

all_walls = []
for i, mid in enumerate(mesh_ids):
    print(f"[{i+1}/{len(mesh_ids)}] Анализ mesh...")
    m = fetch(mid)
    if not m: continue
    verts = parse_verts(m['vertices'][0]['referencedId'])
    walls = get_walls_from_mesh(m, verts)
    all_walls.extend(walls)

print(f"\nСтеновых граней: {len(all_walls)}")

groups = group_walls(all_walls)
print(f"Логических стен: {len(groups)}\n")

commands = []
for g in groups:
    h = max(all_walls[i]['h'] for i in g)
    if h > MIN_WALL_HEIGHT:
        commands.append(make_command(all_walls, g))

print(f"Стен высотой > {MIN_WALL_HEIGHT/1000}м: {len(commands)}\n")

with open(OUTPUT_FILE, 'w') as f:
    for cmd in commands:
        f.write(json.dumps(cmd, ensure_ascii=False) + '\n')

print(f"Сохранено: {OUTPUT_FILE}")
print(f"Команд: {len(commands)}")
