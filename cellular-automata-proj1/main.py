import bpy
import random
import numpy as np

"""
ciekawsze reguły?

DROGI - moze startowac bez drog a losowo ustalac punkty startowe dla drog
na x i na y
a potem za pomoca regul rozszerzac te drogi dopoki nie napotkaja budynku

rozne sasiedztwa?

i oddac to
"""

GRID_SIZE = 20

# frame related settings
frame_duration = 48  # 24 fps?
total_steps = 30  # number of steps to simulate
frame_start = 1
frame_end = frame_start + total_steps * frame_duration - 1

CELLS = {
    "EMPTY": {"STATE": 0, "HEIGHT": 0},
    "HOUSE": {"STATE": 1, "HEIGHT": 1},
    "MEDIUM": {"STATE": 2, "HEIGHT": 3},
    "SKYSCRAPER": {"STATE": 3, "HEIGHT": 6},
    "PARK": {"STATE": 4, "HEIGHT": 0.1},
    "POND": {"STATE": 5, "HEIGHT": 0.01},
    "ROAD": {"STATE": 6, "HEIGHT": 0.01},
}

class Grid():
    def __init__(self, size):
        self.state_grid = np.zeros((size, size), dtype=int)
        self.object_grid = np.zeros_like(self.state_grid, dtype=object) # zeros?
        self.size = size

        # Material definitions
        self.green_material = bpy.data.materials.get("GreenMaterial") or bpy.data.materials.new(name="GreenMaterial")
        self.green_material.diffuse_color = (0, 1, 0, 1)

        self.brown_material = bpy.data.materials.get("BrownMaterial") or bpy.data.materials.new(name="BrownMaterial")
        self.brown_material.diffuse_color = (0.627, 0.322, 0.176, 1)
        
        self.blue_material = bpy.data.materials.get("BlueMaterial") or bpy.data.materials.new(name="BlueMaterial")
        self.blue_material.diffuse_color = (0.212, 0.616, 0.922, 1)

        self.__state_grid_init()
        self.__object_grid_init()

    # Create grid objects once
    def __object_grid_init(self):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 0))
                obj = bpy.context.object
                obj.name = f"GridCube_{i}_{j}"
                self.object_grid[i, j] = obj

    def __state_grid_init(self):
        for i in range(self.size):
            for j in range(self.size):
                self.state_grid[i, j] = CELLS["EMPTY"]["STATE"] if random.random() < 0.75 else CELLS["PARK"]["STATE"]

        self.state_grid[GRID_SIZE//2, 0] = CELLS["ROAD"]["STATE"]
        self.state_grid[0, GRID_SIZE//2] = CELLS["ROAD"]["STATE"]

    def step(self):
        new_grid = self.state_grid.copy()

        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                current_state = self.state_grid[i][j]
                neighbors = [self.state_grid[x][y] 
                             for x in range(max(0, i-1), min(GRID_SIZE, i+2)) 
                             for y in range(max(0, j-1), min(GRID_SIZE, j+2)) 
                             if (x, y) != (i, j)]

                # Forward direction priority for expansion (e.g., expanding rightward and downward)
                if current_state == CELLS["ROAD"]["STATE"]:
                    # Try to expand primarily to the right (j+1) and down (i+1)
                    forward_neighbors = [
                        (i, j + 1),  # Rightward
                        (i + 1, j),  # Downward
                    ]
                    
                    # Expand only if forward neighbor cells are within bounds and empty
                    for x, y in forward_neighbors:
                        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                            new_grid[x][y] = CELLS["ROAD"]["STATE"]
                            break  # Stop after expanding in one forward direction

                # Check rules and update new_grid based on CELLS dict
                if current_state == CELLS["EMPTY"]["STATE"] and CELLS["ROAD"]["STATE"] in neighbors:
                    new_grid[i][j] = CELLS["HOUSE"]["STATE"]
                elif current_state == CELLS["HOUSE"]["STATE"] and neighbors.count(CELLS["HOUSE"]["STATE"]) > 1:
                    new_grid[i][j] = CELLS["MEDIUM"]["STATE"]
                elif current_state == CELLS["MEDIUM"]["STATE"] and neighbors.count(CELLS["MEDIUM"]["STATE"]) > 1:
                    new_grid[i][j] = CELLS["SKYSCRAPER"]["STATE"]
                elif current_state == CELLS["SKYSCRAPER"]["STATE"] and neighbors.count(CELLS["SKYSCRAPER"]["STATE"]) > 1:
                    new_grid[i][j] = CELLS["MEDIUM"]["STATE"]
                elif current_state == CELLS["EMPTY"]["STATE"] and neighbors.count(CELLS["PARK"]["STATE"]) > 2:
                    new_grid[i][j] = CELLS["PARK"]["STATE"]
                elif current_state == CELLS["PARK"]["STATE"] and neighbors.count(CELLS["PARK"]["STATE"]) > 6:
                    new_grid[i][j] = CELLS["POND"]["STATE"]

        self.state_grid = new_grid

    # Update object properties based on grid state
    def update(self, frame):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                obj = self.object_grid[i][j]
                current_state = self.state_grid[i][j]

                obj.hide_viewport = False

                # Update object scale and appearance based on its state
                if current_state == CELLS["EMPTY"]["STATE"]:
                    obj.scale = (1, 1, CELLS["EMPTY"]["HEIGHT"])
                    obj.hide_viewport = True
                elif current_state == CELLS["HOUSE"]["STATE"]:
                    obj.scale = (1, 1, CELLS["HOUSE"]["HEIGHT"])
                    obj.location = (i, j, 0.5)
                elif current_state == CELLS["MEDIUM"]["STATE"]:
                    obj.scale = (1, 1, CELLS["MEDIUM"]["HEIGHT"])
                    obj.location = (i, j, 1.5)
                elif current_state == CELLS["SKYSCRAPER"]["STATE"]:
                    obj.scale = (1, 1, CELLS["SKYSCRAPER"]["HEIGHT"])
                    obj.location = (i, j, 3)
                elif current_state == CELLS["PARK"]["STATE"]:
                    obj.scale = (1, 1, CELLS["PARK"]["HEIGHT"])
                    obj.data.materials.clear()
                    obj.data.materials.append(self.green_material)
                elif current_state == CELLS["ROAD"]["STATE"]:
                    obj.scale = (1, 1, CELLS["ROAD"]["HEIGHT"])
                    obj.data.materials.clear()
                    obj.data.materials.append(self.brown_material)
                elif current_state == CELLS["POND"]["STATE"]:
                    obj.scale = (1, 1, CELLS["POND"]["HEIGHT"])
                    obj.data.materials.clear()
                    obj.data.materials.append(self.blue_material)

                # Insert keyframes for updated properties
                obj.keyframe_insert(data_path="scale", frame=frame)
                obj.keyframe_insert(data_path="location", frame=frame)
                obj.keyframe_insert(data_path="hide_viewport", frame=frame)

# Generate initial grid
grid = Grid(GRID_SIZE)

# Update and animate the grid
for step in range(total_steps):
    frame = frame_start + step * frame_duration
    bpy.context.scene.frame_set(frame)
    grid.update(frame)
    grid.step()

# Set the scene's end frame to match the last animation step
bpy.context.scene.frame_end = frame_end
