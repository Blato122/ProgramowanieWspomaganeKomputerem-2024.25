import bpy
import random
import numpy as np

GRID_SIZE = 20
frame_duration = 12
total_steps = 10

# city elements
EMPTY = 0
HOUSE = 1
MEDIUM_BUILDING = 3
SKYSCRAPER = 6
PARK = 2
POND = 5
ROAD = 4

frame_start = 1
frame_end = frame_start + total_steps * frame_duration - 1

# Materials
green_material = bpy.data.materials.get("ParkMaterial") or bpy.data.materials.new(name="ParkMaterial")
green_material.diffuse_color = (0, 1, 0, 1)

brown_material = bpy.data.materials.get("RoadMaterial") or bpy.data.materials.new(name="RoadMaterial")
brown_material.diffuse_color = (0.627, 0.322, 0.176, 1)

blue_material = bpy.data.materials.get("PondMaterial") or bpy.data.materials.new(name="PondMaterial")
blue_material.diffuse_color = (0, 0, 1, 1)

def initialize_grid(grid):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            grid[i][j] = random.choice([EMPTY, EMPTY, EMPTY, PARK])

    grid[GRID_SIZE//2, :] = ROAD
    grid[:, GRID_SIZE//2] = ROAD

def detect_park_clusters(grid):
    grid_size = len(grid)
    pond_centers = []
    for i in range(1, grid_size - 1):
        for j in range(1, grid_size - 1):
            if all(grid[x][y] == PARK for x in range(i-1, i+2) for y in range(j-1, j+2)):
                pond_centers.append((i, j))
    return pond_centers

def update_grid(grid):
    new_grid = grid.copy()
    pond_centers = detect_park_clusters(grid)

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            current_state = grid[i][j]
            neighbors = [grid[x][y] for x in range(max(0, i-1), min(GRID_SIZE, i+2)) 
                         for y in range(max(0, j-1), min(GRID_SIZE, j+2)) if (x, y) != (i, j)]
            
            if current_state == EMPTY and ROAD in neighbors:
                new_grid[i][j] = HOUSE
            elif current_state == HOUSE:
                if neighbors.count(HOUSE) > 2:
                    new_grid[i][j] = MEDIUM_BUILDING
            elif current_state == MEDIUM_BUILDING:
                if neighbors.count(MEDIUM_BUILDING) > 2:
                    new_grid[i][j] = SKYSCRAPER
            elif current_state == SKYSCRAPER and neighbors.count(PARK) > 2:
                new_grid[i][j] = HOUSE
            elif current_state == PARK and neighbors.count(EMPTY) > 5:
                new_grid[i][j] = PARK

    for (i, j) in pond_centers:
        new_grid[i][j] = POND

    return new_grid

current_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
initialize_grid(current_grid)

grid_objects = []
for i in range(GRID_SIZE):
    row = []
    for j in range(GRID_SIZE):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(i, j, 0))
        obj = bpy.context.object
        obj.name = f"GridObject_{i}_{j}"
        row.append(obj)
    grid_objects.append(row)

def update_grid_objects(grid, frame):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            obj = grid_objects[i][j]
            current_state = grid[i][j]

            if current_state == EMPTY:
                obj.scale = (0.1, 0.1, 0.1)
                obj.hide_viewport = True
            elif current_state == HOUSE:
                obj.scale = (1, 1, 1)
                obj.location = (i, j, 0.5)
                obj.hide_viewport = False
            elif current_state == MEDIUM_BUILDING:
                obj.scale = (1, 1, 3)
                obj.location = (i, j, 1.5)
                obj.hide_viewport = False
            elif current_state == SKYSCRAPER:
                obj.scale = (1, 1, 6)
                obj.location = (i, j, 3)
                obj.hide_viewport = False
            elif current_state == PARK:
                obj.scale = (1, 1, 1)
                obj.hide_viewport = False
                obj.data.materials.clear()
                obj.data.materials.append(green_material)
            elif current_state == POND:
                obj.scale = (1, 1, 0.1)
                obj.hide_viewport = False
                obj.data.materials.clear()
                obj.data.materials.append(blue_material)
            elif current_state == ROAD:
                obj.scale = (1, 1, 0.01)
                obj.hide_viewport = False
                obj.data.materials.clear()
                obj.data.materials.append(brown_material)

            obj.keyframe_insert(data_path="scale", frame=frame)
            obj.keyframe_insert(data_path="location", frame=frame)
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)

for step in range(total_steps):
    frame = frame_start + step * frame_duration
    bpy.context.scene.frame_set(frame)
    update_grid_objects(current_grid, frame)
    current_grid = update_grid(current_grid)

bpy.context.scene.frame_end = frame_end
