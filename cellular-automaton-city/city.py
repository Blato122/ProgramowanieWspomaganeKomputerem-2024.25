import bpy
import random
import numpy as np

GRID_SIZE = 30

# frame related stuff
frame_duration = 12 # 24 fps?
total_steps = 100 # number of steps to simulate
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
    "ACTIVE_ROAD": {"STATE": 7, "HEIGHT": 0.01},
}

COLORS = {
    CELLS["EMPTY"]["STATE"]: (1, 1, 1, 1), # white
    CELLS["HOUSE"]["STATE"]: (0.8, 0.5, 0.2, 1), # brownish
    CELLS["MEDIUM"]["STATE"]: (0.5, 0.5, 0.8, 1), # light blue
    CELLS["SKYSCRAPER"]["STATE"]: (0.1, 0.1, 0.6, 1), # dark blue
    CELLS["PARK"]["STATE"]: (0, 1, 0, 1), # green
    CELLS["ROAD"]["STATE"]: (0.627, 0.322, 0.176, 1), # brown
    CELLS["POND"]["STATE"]: (0.212, 0.616, 0.922, 1), # blue
    CELLS["ACTIVE_ROAD"]["STATE"]: (0, 0, 0, 1), # black so that it can be easily spotted
}

class Grid():
    def __init__(self, size):
        self.state_grid = np.zeros((size, size), dtype=int)
        self.object_grid = np.zeros_like(self.state_grid, dtype=object)
        self.size = size
        
        self.__state_grid_init()
        self.__object_grid_init()
        self.update(frame=frame_start) # I don't think it's necessary

    def __state_grid_init(self):
        for i in range(self.size):
            for j in range(self.size):
                self.state_grid[i, j] = CELLS["EMPTY"]["STATE"] if random.random() < 0.75 else CELLS["PARK"]["STATE"]

        self.state_grid[0, int(GRID_SIZE*1/4)] = CELLS["ACTIVE_ROAD"]["STATE"]
        self.state_grid[0,     GRID_SIZE // 2] = CELLS["ACTIVE_ROAD"]["STATE"]
        self.state_grid[0, int(GRID_SIZE*3/4)] = CELLS["ACTIVE_ROAD"]["STATE"]

    def __object_grid_init(self):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                bpy.ops.mesh.primitive_cube_add(size=1, location=(i, j, 0))
                obj = bpy.context.object
                obj.name = f"GridCube_{i}_{j}"
                self.object_grid[i, j] = obj

                # create material and some node
                # https://blender.stackexchange.com/questions/297185/keyframing-objects-active-material-color-using-python-api <33
                material = bpy.data.materials.new(name=f"CubeMaterial_{i}_{j}")
                material.use_nodes = True
                bsdf = material.node_tree.nodes.get("Principled BSDF")
                bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1) # set a default color
                obj.data.materials.append(material) # assign the material to the object

    def step(self):
        new_grid = self.state_grid.copy()
        skip = [] # :) -> prevents overwriting new ACTIVE_ROAD in the same step (as it is the new_grid that 'knows' about the ACTIVE_ROAD, not the current one (self.state_grid))

        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                current_state = self.state_grid[i][j]
                neighbors = [self.state_grid[x][y]
                             for x in range(max(0, i - 1), min(GRID_SIZE, i + 2))
                             for y in range(max(0, j - 1), min(GRID_SIZE, j + 2))
                             if (x, y) != (i, j)]

                if (i, j) in skip:
                    continue

                if current_state == CELLS["ACTIVE_ROAD"]["STATE"]:
                    x, y = random.choices([(i+1, j), (i, j+1), (i, j-1)], [0.6, 0.2, 0.2])[0]
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        new_grid[i][j] = CELLS["ROAD"]["STATE"]
                        new_grid[x][y] = CELLS["ACTIVE_ROAD"]["STATE"]
                        skip.append((x, y))
                elif (current_state == CELLS["EMPTY"]["STATE"] or current_state == CELLS["PARK"]["STATE"]) and (CELLS["ROAD"]["STATE"] in neighbors or CELLS["ACTIVE_ROAD"]["STATE"] in neighbors):
                    if random.random() < 0.5:
                        new_grid[i][j] = CELLS["HOUSE"]["STATE"]
                elif current_state == CELLS["HOUSE"]["STATE"] and neighbors.count(CELLS["HOUSE"]["STATE"]) > 2:
                    new_grid[i][j] = CELLS["MEDIUM"]["STATE"]
                elif current_state == CELLS["MEDIUM"]["STATE"] and neighbors.count(CELLS["MEDIUM"]["STATE"]) > 1:
                    new_grid[i][j] = CELLS["SKYSCRAPER"]["STATE"]
                elif current_state == CELLS["SKYSCRAPER"]["STATE"] and neighbors.count(CELLS["SKYSCRAPER"]["STATE"]) > 2:
                    new_grid[i][j] = CELLS["MEDIUM"]["STATE"]
                elif current_state == CELLS["EMPTY"]["STATE"] and neighbors.count(CELLS["PARK"]["STATE"]) > 2:
                    new_grid[i][j] = CELLS["PARK"]["STATE"]
                elif current_state == CELLS["PARK"]["STATE"] and neighbors.count(CELLS["PARK"]["STATE"]) > 7:
                    new_grid[i][j] = CELLS["POND"]["STATE"]
                elif current_state == CELLS["POND"]["STATE"] and (neighbors.count(CELLS["PARK"]["STATE"]) + neighbors.count(CELLS["POND"]["STATE"])) < 8:
                    new_grid[i][j] = CELLS["PARK"]["STATE"]

        self.state_grid = new_grid

    def update(self, frame):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                obj = self.object_grid[i][j]
                state = self.state_grid[i][j]

                obj.hide_viewport = False

                if state == CELLS["EMPTY"]["STATE"]:
                    obj.scale = (1, 1, CELLS["EMPTY"]["HEIGHT"])
                    obj.hide_viewport = True
                elif state == CELLS["HOUSE"]["STATE"]:
                    obj.scale = (1, 1, CELLS["HOUSE"]["HEIGHT"])
                    obj.location = (i, j, CELLS["HOUSE"]["HEIGHT"]/2)
                elif state == CELLS["MEDIUM"]["STATE"]:
                    obj.scale = (1, 1, CELLS["MEDIUM"]["HEIGHT"])
                    obj.location = (i, j, CELLS["MEDIUM"]["HEIGHT"]/2)
                elif state == CELLS["SKYSCRAPER"]["STATE"]:
                    obj.scale = (1, 1, CELLS["SKYSCRAPER"]["HEIGHT"])
                    obj.location = (i, j, CELLS["SKYSCRAPER"]["HEIGHT"]/2)
                elif state == CELLS["PARK"]["STATE"]:
                    obj.scale = (1, 1, CELLS["PARK"]["HEIGHT"])
                    obj.location = (i, j, CELLS["PARK"]["HEIGHT"]/2)
                elif state == CELLS["ROAD"]["STATE"]:
                    obj.scale = (1, 1, CELLS["ROAD"]["HEIGHT"])
                    obj.location = (i, j, CELLS["ROAD"]["HEIGHT"]/2)
                elif state == CELLS["POND"]["STATE"]:
                    obj.scale = (1, 1, CELLS["POND"]["HEIGHT"])
                    obj.location = (i, j, CELLS["POND"]["HEIGHT"]/2)
                elif state == CELLS["ACTIVE_ROAD"]["STATE"]:
                    obj.scale = (1, 1, CELLS["ACTIVE_ROAD"]["HEIGHT"])
                    obj.location = (i, j, CELLS["ACTIVE_ROAD"]["HEIGHT"]/2)

                # set the base color for the material and keyframe it
                material = obj.data.materials[0] # get the material assigned to the object
                bsdf = material.node_tree.nodes['Principled BSDF']
                base_color = bsdf.inputs['Base Color']
                base_color.default_value = COLORS[state] # set the color based on the state

                # keyframe the base color
                base_color.keyframe_insert(data_path="default_value", frame=frame)

                # keyframe other properties
                obj.keyframe_insert(data_path="scale", frame=frame)
                obj.keyframe_insert(data_path="location", frame=frame)
                obj.keyframe_insert(data_path="hide_viewport", frame=frame)

grid = Grid(GRID_SIZE)

for step in range(total_steps):
    frame = frame_start + step * frame_duration
    bpy.context.scene.frame_set(frame)
    grid.update(frame)
    grid.step()

bpy.context.scene.frame_end = frame_end

# ENTER MATERIAL PREVIEW MODE