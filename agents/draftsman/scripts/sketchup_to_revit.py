import sys
import json
from specklepy.api.client import SpeckleClient
from specklepy.api import operations
from specklepy.transports.server import ServerTransport

TOKEN_PATH = "/home/axis/openclaw/agents/draftsman/.openclaw/speckle-token.txt"
with open(TOKEN_PATH) as f:
    token = f.read().strip()

client = SpeckleClient(host="app.speckle.systems")
client.authenticate_with_token(token)

project_id = "30eb4c8084"
if len(sys.argv) > 2 and sys.argv[1] == '--project-id':
    project_id = sys.argv[2]

print(f"Connecting to project {project_id}...")
transport = ServerTransport(stream_id=project_id, client=client)

models = client.model.get_models(project_id)
model = models.items[0]
versions = client.version.get_versions(model.id, project_id)
latest_version = versions.items[0]
print(f"Latest version: {latest_version.id}")

ref_obj = getattr(latest_version, "referencedObject", getattr(latest_version, "referenced_object", None))
root = operations.receive(ref_obj, remote_transport=transport)

meshes = []
def find_meshes(obj):
    if not hasattr(obj, "speckle_type"): return
    if obj.speckle_type == "Objects.Geometry.Mesh":
        meshes.append(obj)
    
    if hasattr(obj, "elements") and obj.elements:
        for el in obj.elements:
            find_meshes(el)
    elif hasattr(obj, "@elements") and getattr(obj, "@elements"):
        for el in getattr(obj, "@elements"):
            find_meshes(el)
    
    for k, v in obj.__dict__.items():
        if isinstance(v, list):
            for item in v:
                if hasattr(item, "speckle_type"):
                    find_meshes(item)
        elif hasattr(v, "speckle_type"):
            find_meshes(v)

find_meshes(root)
print(f"Found {len(meshes)} meshes.")
if len(meshes) > 0:
    for i in range(min(5, len(meshes))):
        m = meshes[i]
        vc = len(m.vertices) if m.vertices else 0
        fc = len(m.faces) if m.faces else 0
        print(f"Mesh {i}: {vc} vertices, {fc} face elements")

