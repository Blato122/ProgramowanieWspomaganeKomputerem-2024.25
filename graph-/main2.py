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
    def __init__(self, v1, v2, offset_x=0, offset_y=0, offset_z=0):
        self.v1 = v1
        self.v2 = v2
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.offset_z = offset_z
        
class Graph:
    def __init__(self):
        self.graph = set()
        self.edges = []

    def add_e(self, e):
        self.graph |= set([e.v1, e.v2])
        self.edges.append(e)

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
            elif isinstance(vertex, Table):
                cube.scale = (2, 2, 0.5)

            self.positions[vertex] = {"x": 0, "y": 0, "z": 0} #, "size": size}
            
        for edge in self.edges:
            pos1 = self.positions[edge.v1]
            pos2 = self.positions[edge.v2]
            
            pos2["x"] = pos1["x"] + edge.offset_x
            pos2["y"] = pos1["y"] + edge.offset_y
            pos2["z"] = pos1["z"] + edge.offset_z
                
            obj2 = bpy.data.objects[edge.v2.id]
            obj2.location.x = pos2["x"]
            obj2.location.y = pos2["y"]
            obj2.location.z = pos2["z"]

scene = Scene()
table0 = Table("table0") 
chairs = [Chair(f"chair{i}") for i in range(4)]
scene.add_e(Edge(table0, chairs[0], offset_x=-3.5))
scene.add_e(Edge(table0, chairs[1], offset_x=3.5))
scene.add_e(Edge(table0, chairs[2], offset_y=-3.5))
scene.add_e(Edge(table0, chairs[3], offset_y=3.5))
scene.render()

# czy te klasy są w ogóle potzrbne?
# dodać proste modele, np. krzesło x2, jedno z oparciem zwyklym, deugie z innym. material jakos dynamicznie moze zmienaic i tyle
# potem jeszcze dodac ew szafe i koniec
# obrót dodać, żeby obracać krzesła