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

# frame related stuff
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
        self.object_grid = np.zeros_like(self.state_grid, dtype=int)
        self.size = size

        self.green_material = bpy.data.materials.get("GreenMaterial") or bpy.data.materials.new(name="GreenMaterial")
        self.green_material.diffuse_color = (0, 1, 0, 1)

        self.brown_material = bpy.data.materials.get("BrownMaterial") or bpy.data.materials.new(name="BrownMaterial")
        self.brown_material.diffuse_color = (0.627, 0.322, 0.176, 1)
        
        self.blue_material = bpy.data.materials.get("BlueMaterial") or bpy.data.materials.new(name="BlueMaterial")
        self.blue_material.diffuse_color = (0.212, 0.616, 0.922, 1)

        self.__state_grid_init()
        self.__object_grid_init()

    # create the grid of objects only once
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
                self.state_grid[i, j] = CellState["EMPTY"][0] if random.random() < 0.75 else CellState.PARK

        self.state_grid[GRID_SIZE//2, :] = CellState.ROAD
        self.state_grid[:, GRID_SIZE//2] = CellState.ROAD


    def step(self):
        new_grid = self.state_grid.copy()

        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                current_state = self.state_grid[i][j]
                neighbors = [self.state_grid[x][y] 
                                for x in range(max(0, i-1), min(GRID_SIZE, i+2)) 
                                for y in range(max(0, j-1), min(GRID_SIZE, j+2)) 
                                if (x, y) != (i, j)
                            ]

                # if a cell is EMPTY and there is a ROAD nearby, it transforms into a HOUSE
                if current_state == cell_states["EMPTY"] and CellState.ROAD in neighbors:
                    new_grid[i][j] = CellState.HOUSE
                # if there are two HOUSES next to (diagonally too) each other, they upgrade to MEDIUM_BUILDING
                elif current_state == CellState.HOUSE and neighbors.count(CellState.HOUSE) > 1:
                    new_grid[i][j] = CellState.MEDIUM_BUILDING
                # if there are two MEDIUM_BUILDINGS next to (diagonally too) each other, they upgrade to SKYSCRAPER
                elif current_state == CellState.MEDIUM_BUILDING and neighbors.count(CellState.MEDIUM_BUILDING) > 1:
                    new_grid[i][j] = CellState.SKYSCRAPER
                # if there are two or more SKYSCRAPERS next to (diagonally too) each other, they get downgraded to MEDIUM_BUILDING
                elif current_state == CellState.SKYSCRAPER and neighbors.count(CellState.SKYSCRAPER) > 2:
                    new_grid[i][j] = CellState.MEDIUM_BUILDING
                # if a cell is EMPTY and there are at least 3 PARKS nearby, it becomes a PARK as well
                elif current_state == cell_states["EMPTY"] and neighbors.count(CellState.PARK) > 2:
                    new_grid[i][j] = CellState.PARK
                # if a PARK is surrounded by many other PARKS (7 or 8), its center becomes a POND
                elif current_state == CellState.PARK and neighbors.count(CellState.PARK) > 6:
                    new_grid[i][j] = CellState.POND

        self.state_grid = new_grid #?

    # function to update the properties of the grid objects based on the grid state
    def update(self, frame):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                obj = self.object_grid[i][j]
                current_state = self.state_grid[i][j]

                obj.hide_viewport = False

                # update rhe object based on its state
                if current_state == cell_states["EMPTY"]:
                    obj.scale = (1, 1, 0)
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
                    obj.data.materials.append(self.green_material)
                elif current_state == CellState.ROAD:
                    obj.scale = (1, 1, 0.01)
                    obj.data.materials.clear()
                    obj.data.materials.append(self.brown_material)
                elif current_state == CellState.POND:
                    obj.scale = (1, 1, 0.01)
                    obj.data.materials.clear()
                    obj.data.materials.append(self.blue_material)

                # insert keyframes for the updated properties
                obj.keyframe_insert(data_path="scale", frame=frame)
                obj.keyframe_insert(data_path="location", frame=frame)
                obj.keyframe_insert(data_path="hide_viewport", frame=frame)

# generate the initial grid
grid = Grid(GRID_SIZE)

# update and animate the grid
for step in range(total_steps):
    frame = frame_start + step * frame_duration
    bpy.context.scene.frame_set(frame)
    grid.update(frame)
    grid.step()

# set the scene's end frame to match the last animation step
bpy.context.scene.frame_end = frame_end
