import open3d as o3d
import numpy as np

def compute_centers(mesh):
    vertices = np.asarray(mesh.vertices)
    centroid = vertices.mean(axis=0)
    bbox_center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2.0
    return centroid, bbox_center


# Load OBJ
mesh = o3d.io.read_triangle_mesh("assets/leap_hand/meshes/visual/fingertip.obj")
mesh.compute_vertex_normals()

# Compute centers
centroid, bbox_center = compute_centers(mesh)

print("Centroid:", centroid)
print("Bounding box center:", bbox_center)

# Create small spheres to mark centers
centroid_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.01)
centroid_sphere.paint_uniform_color([1, 0, 0])  # red
centroid_sphere.translate(centroid)

bbox_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.01)
bbox_sphere.paint_uniform_color([0, 1, 0])  # green
bbox_sphere.translate(bbox_center)

# Coordinate frame at mesh origin
frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.05)

# Visualize
o3d.visualization.draw_geometries([
    mesh,
    centroid_sphere,
    bbox_sphere,
    frame
])