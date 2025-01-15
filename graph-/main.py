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
    def __init__(self, v1, v2, directed=False, offset_left=None, offset_right=None, offset_up=None, offset_down=None):
        self.v1 = v1
        self.v2 = v2
        self.directed = directed
        
class Graph:
    def __init__(self):
        self.graph = defaultdict(set)

    def add_e(self, e):
        self.graph[e.v1].add(e.v2)
        if not e.directed:
            self.graph[e.v2].add(e.v1)

class Scene(Graph):
    def __init__(self):
        super.__init__()

    def render(self):
        for furniture in self._graph:
            obj = bpy.data.objects.new(furniture.id, None)
            bpy.context.collection.objects.link(obj)

scene = Scene()
chair = Chair()
table = Table()
scene.add_e(Edge(chair, table, offset_right=1))

scene.render()