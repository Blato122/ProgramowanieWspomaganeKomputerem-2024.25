import bpy
import random
import numpy as np

GRID_SIZE = 6
frame_duration = 12  # 0.5 seconds at 24 fps
total_steps = 10  # Number of steps to simulate

# city elements (grid tile states)
EMPTY = 0
HOUSE = 1
SKYSCRAPER = 2
PARK = 3
ROAD = 4

frame_start = 1
frame_end = frame_start + total_steps * frame_duration - 1

# Materials
green_material = bpy.data.materials.get("ParkMaterial") or bpy.data.materials.new(name="ParkMaterial")
green_material.diffuse_color = (0, 1, 0, 1)  # Green for parks

brown_material = bpy.data.materials.get("RoadMaterial") or bpy.data.materials.new(name="RoadMaterial")
brown_material.diffuse_color = (0.627, 0.322, 0.176, 1)  # Brown for roads

# Initialize the grid state
def initialize_grid(grid):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            grid[i][j] = random.choice([EMPTY, EMPTY, EMPTY, PARK])

    # Create a horizontal and vertical road
    grid[GRID_SIZE//2, :] = ROAD
    grid[:, GRID_SIZE//2] = ROAD

# Update the grid based on cellular automata rules
def update_grid(grid):
    new_grid = grid.copy()
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            current_state = grid[i][j]
            neighbors = [grid[x][y] for x in range(max(0, i-1), min(GRID_SIZE, i+2)) 
                         for y in range(max(0, j-1), min(GRID_SIZE, j+2)) if (x, y) != (i, j)]
            if current_state == EMPTY and ROAD in neighbors:
                new_grid[i][j] = HOUSE
            elif current_state == HOUSE and neighbors.count(HOUSE) > 1:
                new_grid[i][j] = SKYSCRAPER
            elif current_state == SKYSCRAPER and neighbors.count(PARK) > 2:
                new_grid[i][j] = HOUSE
            elif current_state == PARK and neighbors.count(EMPTY) > 0:
                new_grid[i][j] = PARK
    return new_grid

# Generate initial grid
current_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
initialize_grid(current_grid)

# Create the grids and set keyframes
for step in range(total_steps):
    frame = frame_start + step * frame_duration
    bpy.context.scene.frame_set(frame)

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            current_state = current_grid[i][j]
            obj = None
            
            # Create new geometry for each frame based on the state of the cell
            if current_state == HOUSE:
                bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 0.5))
                obj = bpy.context.object
            elif current_state == SKYSCRAPER:
                bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 3), scale=(1, 1, 6))
                obj = bpy.context.object
            elif current_state == PARK:
                bpy.ops.mesh.primitive_plane_add(size=1, location=(i, j, 0))
                obj = bpy.context.object
                obj.data.materials.append(green_material)
            elif current_state == ROAD:
                bpy.ops.mesh.primitive_plane_add(size=1, location=(i, j, 0.1))
                obj = bpy.context.object
                obj.data.materials.append(brown_material)

            # Ensure the object exists before setting keyframes
            if obj:
                obj.keyframe_insert(data_path="hide_viewport", frame=frame)
                obj.hide_viewport = True  # Hide it after this step's duration
                obj.keyframe_insert(data_path="hide_viewport", frame=frame + frame_duration)

    # Move to the next state
    current_grid = update_grid(current_grid)

# Set the scene's end frame to match the last animation step
bpy.context.scene.frame_end = frame_end
