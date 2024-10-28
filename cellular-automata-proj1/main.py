import bpy
import random
import numpy as np

grid_size = 50 # size of the grid
iterations = 100 # total number of iterations/frames
current_iteration = 0 # start at the first frame

# city elements (grid tile states)
EMPTY = 0
HOUSE = 1
SKYSCRAPER = 2
PARK = 3
ROAD = 4

# initializing the grid
grid = np.zeros((grid_size, grid_size)) # zeros => EMPTY
grid_states = [] # to store the grid states for each frame

frame_duration = 48 # 2 seconds at 24 fps
total_steps = 100

# set the start and the end frame
frame_start = 1
frame_end = total_steps * frame_duration

# starting conditions: mostly empty land, some roads and parks
# TO CHYBA NIE DZIAŁA TAK JAK MI SIĘ WYDAEJ XD
def initialize_grid(grid):
    for i in range(grid_size):
        for j in range(grid_size):
            grid[i][j] = random.choice([EMPTY, EMPTY, EMPTY, PARK])  # mostly empty land and maybe a few parks

    # create a horizontal road in the middle
    grid[grid_size//2, range(grid_size)] = ROAD
    # and an extra road
    grid[range(grid_size//2), grid_size//2] = ROAD

# update the grid based on cellular automata rules
def update_grid(grid):
    new_grid = grid.copy()

    for i in range(grid_size):
        for j in range(grid_size):
            current_state = grid[i][j]
            
            # Get neighboring cells
            neighbors = [grid[x][y] for x in range(max(0, i-1), min(grid_size, i+2)) 
                                    for y in range(max(0, j-1), min(grid_size, j+2)) 
                                    if (x, y) != (i, j)]
            
            # Rule: If the cell is empty and near a road, it might turn into a house
            if current_state == EMPTY:
                if ROAD in neighbors:
                    new_grid[i][j] = HOUSE
            
            # Rule: Houses surrounded by many houses upgrade to skyscrapers
            elif current_state == HOUSE:
                if neighbors.count(HOUSE) > 4:
                    new_grid[i][j] = SKYSCRAPER
            
            # Rule: Skyscrapers near too many parks might downgrade to houses
            elif current_state == SKYSCRAPER:
                if neighbors.count(PARK) > 2:
                    new_grid[i][j] = HOUSE
            
            # Rule: Parks remain parks
            elif current_state == PARK:
                if neighbors.count(EMPTY) > 5:
                    new_grid[i][j] = PARK  # Parks remain unchanged

    return new_grid

initialize_grid(grid)

# green material for parks
green_material = bpy.data.materials.new(name="ParkMaterial")
green_material.diffuse_color = (0, 1, 0, 1)  # RGBA for green color

# brown material for roads
brown_material = bpy.data.materials.new(name="RoadMaterial")
brown_material.diffuse_color = (0.627, 0.322, 0.176, 1)  # RGBA for brown color

# Clear existing objects in the scene (only the city objects)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

for step in range(total_steps):
    frame = frame_start + step * frame_duration  # Calculate the frame for the current step
    bpy.context.scene.frame_set(frame)  # Set the current frame

    for i in range(grid_size):
        for j in range(grid_size):
            current_state = grid[i][j]
            
            # Create geometry based on the state of the cell
            if current_state == HOUSE:
                bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 0.5))
            elif current_state == SKYSCRAPER:
                bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 3), scale=(1, 1, 6))
            elif current_state == PARK:
                bpy.ops.mesh.primitive_plane_add(size=1, location=(i, j, 0))
                bpy.context.object.data.materials.append(green_material)  # Apply green material to parks
            elif current_state == ROAD:
                bpy.ops.mesh.primitive_plane_add(size=1, location=(i, j, 0.1))
                bpy.context.object.data.materials.append(brown_material)  # Apply brown material to roads
                bpy.context.object.scale[2] = 0.01  # Thin road

            # Get the last created object
            obj = bpy.context.object
            
            # Insert keyframes for visibility (optional)
            obj.hide_viewport = False  # Make sure the object is visible
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)

            # Optionally hide the object in previous frames
            if frame > frame_start:
                obj.hide_viewport = True
                obj.keyframe_insert(data_path="hide_viewport", frame=frame - frame_duration)

    grid = update_grid(grid)

# Set the end frame for the animation
bpy.context.scene.frame_end = frame_end