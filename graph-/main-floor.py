import bpy
from collections import defaultdict
import math

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

class Lamp(Vertex):
    def __init__(self, id, number_of_bulbs=2, material="wood", shade_type="regular"):
        super().__init__(id)
        self.number_of_bulbs = number_of_bulbs
        self.material = material
        self.shade_type = shade_type

class Floor(Vertex):
    def __init__(self, id, size=10, tiles=8, light_color=(0.8, 0.8, 0.8, 1), dark_color=(0.2, 0.2, 0.2, 1)):
        super().__init__(id)
        self.size = size
        self.tiles = tiles
        self.light_color = light_color
        self.dark_color = dark_color

class Edge:
    def __init__(self, v1, v2, offset_x=0, offset_y=0, offset_z=0, rotation=0):
        self.v1 = v1
        self.v2 = v2
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.offset_z = offset_z
        self.rotation = rotation
        
class Graph:
    def __init__(self):
        self.graph = set()
        self.edges = []

    def add_e(self, e):
        self.graph |= set([e.v1, e.v2])
        self.edges.append(e)

def create_wood_material(name, color):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    
    # Clear default nodes
    nodes.clear()
    
    # Create node setup for wood material
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    output = nodes.new('ShaderNodeOutputMaterial')
    
    # Set wood color
    diffuse.inputs[0].default_value = color
    
    # Link nodes
    material.node_tree.links.new(diffuse.outputs[0], output.inputs[0])
    
    return material

def create_table(name):
    # Create table top
    bpy.ops.mesh.primitive_cube_add()
    top = bpy.context.active_object
    top.name = f"{name}"
    top.scale = (2, 2, 0.1)
    top.location = (0, 0, 1)
    
    # Create legs
    legs = []
    positions = [(1.8, 1.8, 0), (-1.8, 1.8, 0), (1.8, -1.8, 0), (-1.8, -1.8, 0)]
    for i, pos in enumerate(positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=3)
        leg = bpy.context.active_object
        leg.name = f"{name}_leg_{i}"
        leg.location = (pos[0], pos[1], -0.5)
        legs.append(leg)
    
    # Join all parts
    for leg in legs:
        leg.select_set(True)
    top.select_set(True)
    bpy.context.view_layer.objects.active = top
    bpy.ops.object.join()

    # Create and apply wood material
    wood_material = create_wood_material(f"{name}_material", (0.4, 0.2, 0.1, 1))
    top.data.materials.append(wood_material)

    return top

def create_chair(name):
    # Create seat
    bpy.ops.mesh.primitive_cube_add()
    seat = bpy.context.active_object
    seat.name = f"{name}"
    seat.scale = (1, 1, 0.1)
    
    # Create backrest
    bpy.ops.mesh.primitive_cube_add()
    back = bpy.context.active_object
    back.name = f"{name}_back"
    back.scale = (1, 0.1, 1)
    back.location = (0, -1, 1)
    
    # Create legs
    legs = []
    positions = [(0.8, 0.8, 0), (-0.8, 0.8, 0), (0.8, -0.8, 0), (-0.8, -0.8, 0)]
    for i, pos in enumerate(positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2)
        leg = bpy.context.active_object
        leg.name = f"{name}_leg_{i}"
        leg.location = (pos[0], pos[1], -1)
        legs.append(leg)
    
    # Join all parts
    for leg in legs:
        leg.select_set(True)
    back.select_set(True)
    seat.select_set(True)
    bpy.context.view_layer.objects.active = seat
    bpy.ops.object.join()

    # Create and apply wood material (lighter color for chairs)
    wood_material = create_wood_material(f"{name}_material", (0.6, 0.3, 0.1, 1))
    seat.data.materials.append(wood_material)
    
    return seat

def create_lamp_material(name, is_emissive=False):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    
    if is_emissive:
        # Emission material for lampshade
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs[0].default_value = (1, 0.9, 0.7, 1)  # Warm light
        emission.inputs[1].default_value = 2.0  # Strength
        output = nodes.new('ShaderNodeOutputMaterial')
        material.node_tree.links.new(emission.outputs[0], output.inputs[0])
    else:
        # Metallic material for base
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.inputs['Metallic'].default_value = 0.9
        principled.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)
        output = nodes.new('ShaderNodeOutputMaterial')
        material.node_tree.links.new(principled.outputs[0], output.inputs[0])
    
    return material

def create_lamp(name):
    # Create base
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.1)
    base = bpy.context.active_object
    base.name = f"{name}"
    base.location = (0, 0, 0)
    
    # Create stand
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2)
    stand = bpy.context.active_object
    stand.name = f"{name}_stand"
    stand.location = (0, 0, 1)
    
    # Create shade
    bpy.ops.mesh.primitive_cone_add(radius1=0.8, radius2=0.4, depth=0.8)
    shade = bpy.context.active_object
    shade.name = f"{name}_shade"
    shade.location = (0, 0, 2)
    
    # Join all parts
    stand.select_set(True)
    shade.select_set(True)
    base.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
    
    # Apply materials
    base_material = create_lamp_material(f"{name}_base_material")
    shade_material = create_lamp_material(f"{name}_shade_material", is_emissive=True)
    
    base.data.materials.append(base_material)
    base.data.materials.append(shade_material)
    
    return base

def create_floor_materials():
    # Light tile
    light_material = bpy.data.materials.new(name="floor_light")
    light_material.use_nodes = True
    light_material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
    
    # Dark tile
    dark_material = bpy.data.materials.new(name="floor_dark")
    dark_material.use_nodes = True
    dark_material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.2, 0.2, 0.2, 1)
    
    return light_material, dark_material

def create_floor(name, size=10, tiles=8, light_color=(0.8, 0.8, 0.8, 1), dark_color=(0.2, 0.2, 0.2, 1)):
    # Create plane
    bpy.ops.mesh.primitive_plane_add(size=size)
    floor = bpy.context.active_object
    floor.name = name
    
    # Subdivide into tiles x tiles grid
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=tiles-1)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create materials
    light_material = bpy.data.materials.new(name=f"{name}_light")
    light_material.use_nodes = True
    light_material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = light_color
    
    dark_material = bpy.data.materials.new(name=f"{name}_dark")
    dark_material.use_nodes = True
    dark_material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = dark_color
    
    floor.data.materials.append(light_material)
    floor.data.materials.append(dark_material)
    
    # Apply checkerboard pattern
    for i, face in enumerate(floor.data.polygons):
        row = i // tiles
        col = i % tiles
        face.material_index = (row + col) % 2
    
    return floor

class Scene(Graph):
    def __init__(self):
        super().__init__()
        self.positions = {}

    def render(self):
        for vertex in self.graph:
            if isinstance(vertex, Chair):
                obj = create_chair(vertex.id)
            elif isinstance(vertex, Table):
                obj = create_table(vertex.id)
            elif isinstance(vertex, Lamp):
                obj = create_lamp(vertex.id)
            elif isinstance(vertex, Floor):
                obj = create_floor(vertex.id)
            
            self.positions[vertex] = {"x": 0, "y": 0, "z": 0}
            
        for edge in self.edges:
            pos1 = self.positions[edge.v1]
            pos2 = self.positions[edge.v2]
            
            pos2["x"] = pos1["x"] + edge.offset_x
            pos2["y"] = pos1["y"] + edge.offset_y
            pos2["z"] = pos1["z"] + edge.offset_z
            pos2["rotation"] = edge.rotation
                
            obj2 = bpy.data.objects[edge.v2.id]
            obj2.location.x = pos2["x"]
            obj2.location.y = pos2["y"]
            obj2.location.z = pos2["z"]
            obj2.rotation_euler[2] = math.radians(pos2["rotation"])

scene = Scene()
floor0 = Floor("floor0")
table0 = Table("table0") 
lamps = [Lamp(f"lamp{i}") for i in range(4)]
chairs = [Chair(f"chair{i}") for i in range(4)]

scene.add_e(Edge(floor0, table0, offset_z=3))
scene.add_e(Edge(table0, chairs[0], offset_x=-3.5, rotation=270, offset_z=-1))
scene.add_e(Edge(table0, chairs[1], offset_x=3.5, rotation=90, offset_z=-1))
scene.add_e(Edge(table0, chairs[2], offset_y=-3.5, rotation=0, offset_z=-1))
scene.add_e(Edge(table0, chairs[3], offset_y=3.5, rotation=180, offset_z=-1))
scene.add_e(Edge(table0, lamps[0], offset_z=0.2, offset_x=-1))
scene.add_e(Edge(lamps[0], lamps[1], offset_x=2))
scene.render()

# czy te klasy są w ogóle potzrbne?
# dodać proste modele, np. krzesło x2, jedno z oparciem zwyklym, deugie z innym. material jakos dynamicznie moze zmienaic i tyle
# potem jeszcze dodac ew szafe i koniec
# obrót dodać, żeby obracać krzesła