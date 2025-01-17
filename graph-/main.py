import bpy
from collections import defaultdict

# for k, v in attrs:
#     setattr(self, k, v)

class Vertex:
    def __init__(self, id):
        self.id = id

class Chair(Vertex):
    def __init__(self, id, number_of_legs=4, material="wood", back_type="regular"):
        super().__init__(id)
        self.number_of_legs = number_of_legs
        self.material = material
        self.back_type = back_type

class Table(Vertex):
    def __init__(self, id, number_of_legs=4, material="wood", table_type="regular"):
        super().__init__(id)
        self.number_of_legs = number_of_legs
        self.material = material
        self.table_type = table_type

class Edge:
    def __init__(self, v1, v2, directed=True, offset_left=None, offset_right=None, offset_up=None, offset_down=None):
        self.v1 = v1
        self.v2 = v2
        self.directed = directed
        self.offset_left = offset_left
        self.offset_right = offset_right 
        self.offset_up = offset_up
        self.offset_down = offset_down
        
class Graph:
    def __init__(self):
        self.graph = defaultdict(list)
        self.edges = []

    def add_e(self, e):
        self.graph[e.v1].append((e.v2, e))  # Store edge object
        self.edges.append(e)
        if not e.directed:
            self.graph[e.v2].append((e.v1, e))

class Scene(Graph):
    def __init__(self):
        super().__init__()
        self.positions = {}

    def render(self):
        for vertex in self.graph:
            bpy.ops.mesh.primitive_cube_add()
            cube = bpy.context.active_object
            cube.name = vertex.id
            
            if isinstance(vertex, Chair):
                cube.scale = (1, 1, 1)
                size = 2
            elif isinstance(vertex, Table):
                cube.scale = (2, 2, 0.5)
                size = 4

            self.positions[vertex] = {"x": 0, "z": 0, "size": size}
            
        for edge in self.edges:
            pos1 = self.positions[edge.v1]
            pos2 = self.positions[edge.v2]
            
            if edge.offset_right:
                pos2["x"] = pos1["x"] + edge.offset_right * pos1["size"]
            if edge.offset_left:
                pos2["x"] = pos1["x"] - edge.offset_left * pos1["size"]
            if edge.offset_up:
                pos2["z"] = pos1["z"] + edge.offset_up * pos1["size"]
            if edge.offset_down:
                pos2["z"] = pos1["z"] - edge.offset_down * pos1["size"]
                
            obj2 = bpy.data.objects[edge.v2.id]
            obj2.location.x = pos2["x"]
            obj2.location.z = pos2["z"]

            # obj1 = bpy.data.objects[edge.v1.id]
            # obj2 = bpy.data.objects[edge.v2.id]
            
            # if edge.offset_right:
            #     obj2.location.x = obj1.location.x + edge.offset_right
            # if edge.offset_left:
            #     obj2.location.x = obj1.location.x - edge.offset_left
            # if edge.offset_up:
            #     obj2.location.z = obj1.location.z + edge.offset_up
            # if edge.offset_down:
            #     obj2.location.z = obj1.location.z - edge.offset_down

scene = Scene()
chair1 = Chair("chair1")
table1 = Table("table1") 
chair2 = Chair("chair2")
chair3 = Chair("chair3")
scene.add_e(Edge(table1, chair1, offset_right=2))
scene.add_e(Edge(table1, chair2, offset_left=2))
scene.add_e(Edge(chair2, chair3, offset_up=2))
scene.render()