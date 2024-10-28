import bpy
import random
import numpy as np
from enum import Enum

"""
to do: przenieść resztę do klasy Grid
ciekawsze reguły?
detect park clusters

np.full

cellstate jako jakas wewnetrzna klasa??? nib nie... i niby enum bad...

wysokosci typu 3, 6 do zmiennych

blender na laptopa

i oddac to

i zapytac o termin za 2 tyg
"""

GRID_SIZE = 20

# frame related stuff
frame_duration = 48  # 24 fps?
total_steps = 30  # Number of steps to simulate
frame_start = 1
frame_end = frame_start + total_steps * frame_duration - 1

# city elements (grid cell states)
class CellState(Enum):
    EMPTY = 0
    HOUSE = 1
    MEDIUM_BUILDING = 2
    SKYSCRAPER = 3
    PARK = 4
    POND = 5
    ROAD = 6

# class Grid():
#     def __init__(self, size):
#         self.state_grid = np.full((size, size), CellState.EMPTY, dtype=object)
#         self.object_grid = np.zeros_like(self.state_grid)
#         self.size = size

#         for i in range(size):
#             for j in range(size):
#                 self.state_grid[i, j] = CellState.EMPTY if random.random() < 0.75 else CellState.PARK

#         # create a horizontal and vertical road
#         self.state_grid[GRID_SIZE//2, :] = CellState.ROAD
#         self.state_grid[:, GRID_SIZE//2] = CellState.ROAD

# materials
green_material = bpy.data.materials.get("ParkMaterial") or bpy.data.materials.new(name="ParkMaterial")
green_material.diffuse_color = (0, 1, 0, 1)

brown_material = bpy.data.materials.get("RoadMaterial") or bpy.data.materials.new(name="RoadMaterial")
brown_material.diffuse_color = (0.627, 0.322, 0.176, 1)

blue_material = bpy.data.materials.get("PondMaterial") or bpy.data.materials.new(name="PondMaterial")
blue_material.diffuse_color = (0.212, 0.616, 0.922, 1)

# initialize the grid state
def initialize_grid(grid):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            grid[i][j] = random.choice([CellState.EMPTY, CellState.EMPTY, CellState.EMPTY, CellState.PARK])

    # create a horizontal and vertical road
    grid[GRID_SIZE//2, :] = CellState.ROAD
    grid[:, GRID_SIZE//2] = CellState.ROAD

# Update the grid based on cellular automata rules
def update_grid(grid):
    new_grid = grid.copy()
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            current_state = grid[i][j]
            neighbors = [grid[x][y] for x in range(max(0, i-1), min(GRID_SIZE, i+2)) 
                         for y in range(max(0, j-1), min(GRID_SIZE, j+2)) if (x, y) != (i, j)]

            # if all(neighbors == CellState.PARK)

            if current_state == CellState.EMPTY and CellState.ROAD in neighbors:
                new_grid[i][j] = CellState.HOUSE
            elif current_state == CellState.HOUSE and neighbors.count(CellState.HOUSE) > 1:
                new_grid[i][j] = CellState.MEDIUM_BUILDING
            elif current_state == CellState.MEDIUM_BUILDING and neighbors.count(CellState.MEDIUM_BUILDING) > 1:
                new_grid[i][j] = CellState.SKYSCRAPER
            elif current_state == CellState.SKYSCRAPER and neighbors.count(CellState.SKYSCRAPER) > 1:
                new_grid[i][j] = CellState.HOUSE
            elif current_state == CellState.EMPTY and neighbors.count(CellState.PARK) > 1:
                new_grid[i][j] = CellState.PARK
            elif current_state == CellState.PARK and neighbors.count(CellState.PARK) > 6:
                new_grid[i][j] = CellState.POND

    return new_grid

# can be done above
# def detect_park_clusters(grid) -> list:
#     for x in range(GRID_SIZE):
#         for y in range(GRID_SIZE):
#             nbrs = [nx, ny for nx in range(max(0, x-1), min())]
#             if all(nbrs)


# generate the initial grid
current_grid = np.full((GRID_SIZE, GRID_SIZE), CellState.EMPTY, dtype=object)
initialize_grid(current_grid)

# create the grid of objects only once
grid_objects = []
for i in range(GRID_SIZE):
    row = []
    for j in range(GRID_SIZE):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 0))
        obj = bpy.context.object
        obj.name = f"GridCube_{i}_{j}"
        row.append(obj)
    grid_objects.append(row)

# function to update the properties of the grid objects based on the grid state
def update_grid_objects(grid, frame):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            obj = grid_objects[i][j]
            current_state = grid[i][j]

            obj.hide_viewport = False

            # update object based on state
            if current_state == CellState.EMPTY:
                obj.scale = (0.1, 0.1, 0.1)
                obj.hide_viewport = True
            elif current_state == CellState.HOUSE:
                obj.scale = (1, 1, 1)
                obj.location = (i, j, 0.5)
            elif current_state == CellState.MEDIUM_BUILDING:
                obj.scale = (1, 1, 3)
                obj.location = (i, j, 1.5)
            elif current_state == CellState.SKYSCRAPER:
                obj.scale = (1, 1, 6)
                obj.location = (i, j, 3)
            elif current_state == CellState.PARK:
                obj.scale = (1, 1, 0.1)
                obj.data.materials.clear()
                obj.data.materials.append(green_material)
            elif current_state == CellState.ROAD:
                obj.scale = (1, 1, 0.01)
                obj.data.materials.clear()
                obj.data.materials.append(brown_material)
            elif current_state == CellState.POND:
                obj.scale = (1, 1, 0.01)
                obj.data.materials.clear()
                obj.data.materials.append(blue_material)

            # insert keyframes for the updated properties
            obj.keyframe_insert(data_path="scale", frame=frame)
            obj.keyframe_insert(data_path="location", frame=frame)
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)

# update and animate the grid
for step in range(total_steps):
    frame = frame_start + step * frame_duration
    bpy.context.scene.frame_set(frame)

    # update the grid objects based on the current grid state
    update_grid_objects(current_grid, frame)

    # move to the next state
    current_grid = update_grid(current_grid)

# set the scene's end frame to match the last animation step
bpy.context.scene.frame_end = frame_end
