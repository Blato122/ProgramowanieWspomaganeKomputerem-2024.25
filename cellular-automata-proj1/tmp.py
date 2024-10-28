import bpy
import random
import numpy as np

GRID_SIZE = 20
# Set the frame duration for each step
frame_duration = 48  # 2 seconds at 24 fps
total_steps = 10  # Number of steps to simulate

# city elements (grid tile states)
EMPTY = 0
HOUSE = 1
SKYSCRAPER = 2
PARK = 3
ROAD = 4

# Set the start and end frame
frame_start = 1
frame_end = total_steps * frame_duration

# store all grid objects for visibility keyframes
grid_objects = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)] # NUMPY
# create the grid over time
current_grid = np.zeros((GRID_SIZE, GRID_SIZE))
# initial grid state
def initialize_grid(grid):
    grid_size = len(grid)
    for i in range(grid_size):
        for j in range(grid_size):
            grid[i][j] = random.choice([EMPTY, EMPTY, EMPTY, PARK])  # mostly empty land and maybe a few parks

    # create a horizontal road in the middle
    grid[grid_size//2, range(grid_size)] = ROAD
    # and an extra road
    grid[range(grid_size//2), grid_size//2] = ROAD
initialize_grid(current_grid)

# update the grid based on cellular automata rules
def update_grid(grid):
    new_grid = grid.copy()
    grid_size = len(new_grid)

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
                if neighbors.count(HOUSE) > 2:
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

# green material for parks
green_material = bpy.data.materials.new(name="ParkMaterial")
green_material.diffuse_color = (0, 1, 0, 1)  # RGBA for green color

# brown material for roads
brown_material = bpy.data.materials.new(name="RoadMaterial")
brown_material.diffuse_color = (0.627, 0.322, 0.176, 1)  # RGBA for brown color

for step in range(total_steps):
    frame = frame_start + step * frame_duration  # Calculate the frame for the current step
    bpy.context.scene.frame_set(frame)  # Set the current frame

    # Create or update geometry for the current state
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            current_state = current_grid[i][j]

            # Check if an object already exists for this grid cell
            if grid_objects[i][j] is None:
                # Create new geometry based on the state of the cell
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

                # Assign the object to the grid_objects array
                grid_objects[i][j] = bpy.context.object
            else: # WHAT?!?!
                # Update the position and scale for existing objects based on the state
                obj = grid_objects[i][j]
                if current_state == HOUSE:
                    obj.location = (i, j, 0.5)
                    obj.scale = (1, 1, 1)
                elif current_state == SKYSCRAPER:
                    obj.location = (i, j, 3)
                    obj.scale = (1, 1, 6)
                elif current_state == PARK:
                    obj.location = (i, j, 0)
                elif current_state == ROAD:
                    obj.location = (i, j, 0.1)

            # Insert keyframes for visibility (optional)
            obj = grid_objects[i][j]
            obj.hide_viewport = False  # Make sure the object is visible
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)

            # Optionally hide the object in previous frames
            if frame > frame_start:
                obj.hide_viewport = True
                obj.keyframe_insert(data_path="hide_viewport", frame=frame - frame_duration)

    # Calculate the next grid state
    current_grid = update_grid(current_grid)

# Set the end frame for the animation
bpy.context.scene.frame_end = frame_end
