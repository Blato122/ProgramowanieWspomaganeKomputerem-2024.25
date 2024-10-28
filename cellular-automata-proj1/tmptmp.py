import bpy
import random

# Define constants for the grid and the states
GRID_SIZE = 6  # Grid size
HOUSES = 0
SKYSCRAPERS = 1

# Function to determine the next state based on the current grid
def next_grid_state(grid):
    new_grid = [[HOUSES for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == HOUSES:
                # Check for adjacent houses
                adjacent_houses = 0
                if i > 0 and grid[i - 1][j] == HOUSES:  # Up
                    adjacent_houses += 1
                if i < GRID_SIZE - 1 and grid[i + 1][j] == HOUSES:  # Down
                    adjacent_houses += 1
                if j > 0 and grid[i][j - 1] == HOUSES:  # Left
                    adjacent_houses += 1
                if j < GRID_SIZE - 1 and grid[i][j + 1] == HOUSES:  # Right
                    adjacent_houses += 1
                
                # If there are 2 adjacent houses, turn one into a skyscraper
                if adjacent_houses >= 2:
                    new_grid[i][j] = SKYSCRAPERS
                else:
                    new_grid[i][j] = HOUSES
            else:
                new_grid[i][j] = SKYSCRAPERS  # Keep existing skyscrapers
    return new_grid

# Set the frame duration for each step
frame_duration = 48  # 2 seconds at 24 fps
total_steps = 10  # Number of steps to simulate

# Set the start and end frame
frame_start = 1
frame_end = total_steps * frame_duration

# Store all grid objects for visibility keyframes
grid_objects = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# Create the grid over time
current_grid = [[HOUSES for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # Initial grid state

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
                if current_state == HOUSES:
                    bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 0.5))
                elif current_state == SKYSCRAPERS:
                    bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 3), scale=(1, 1, 6))

                # Assign the object to the grid_objects array
                grid_objects[i][j] = bpy.context.object
            else:
                # Update the position and scale for existing objects based on the state
                obj = grid_objects[i][j]
                if current_state == HOUSES:
                    obj.location = (i, j, 0.5)
                    obj.scale = (1, 1, 1)
                elif current_state == SKYSCRAPERS:
                    obj.location = (i, j, 3)
                    obj.scale = (1, 1, 6)

            # Insert keyframes for visibility (optional)
            obj = grid_objects[i][j]
            obj.hide_viewport = False  # Make sure the object is visible
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)

            # Optionally hide the object in previous frames
            if frame > frame_start:
                obj.hide_viewport = True
                obj.keyframe_insert(data_path="hide_viewport", frame=frame - frame_duration)

    # Calculate the next grid state
    current_grid = next_grid_state(current_grid)

# Set the end frame for the animation
bpy.context.scene.frame_end = frame_end
