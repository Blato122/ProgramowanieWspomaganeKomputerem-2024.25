import bpy
import random
import math

# GA hyperparameters
population_size = 100
generations = 10
mutation_rate = 0.2
tournament_size = 3

view_vehicle_duration = 48
total_frames = generations * view_vehicle_duration

scenario = 'race'

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_plane():
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, -3))
    plane = bpy.context.active_object
    
    mat = bpy.data.materials.new(name="Ground")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_image = nodes.new('ShaderNodeTexImage')
    
    tex_image.image = bpy.data.images.load(r"C:\wsl2\home\blato\everything\ProgramowanieWspomaganeKomputerem-2024.25\genetic-algorithm-car\asphalt-texture.jpg")

    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 1.0
    
    links.new(tex_coord.outputs['UV'], tex_image.inputs['Vector'])
    links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    plane.data.materials.append(mat)

def unpack_genes(genes):
    return (
        genes["vehicle_type"],
        genes["continuous"]["body_width"],
        genes["continuous"]["body_height"],
        genes["continuous"]["body_length"],
        genes["continuous"]["wheel_thickness"],
        genes["binary"]["is_red"],
        genes["binary"]["has_spoiler"],
        genes["binary"]["has_bullbar"],
        genes["roof_rack"]["has_poles"],
        genes["roof_rack"]["has_modules"]
    )

def load_vehicle(genes, frame, offset=0):
    vehicle_type, body_width, body_height, body_length, wheel_thickness, is_red, has_spoiler, has_bullbar, \
         has_poles, has_modules = unpack_genes(genes)
    # filepath = f"{vehicle_type}.blend"
    filepath = f"C:\\wsl2\\home\\blato\\everything\\ProgramowanieWspomaganeKomputerem-2024.25\\genetic-algorithm-car\\{vehicle_type}.blend"
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects]
    
    # new!
    collection_name = f"Vehicle_{frame // view_vehicle_duration}"
    vehicle_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(vehicle_collection)

    # main parts:
    body = None
    wheels = []

    # addons:
    spoiler = None
    bullbar = None
    
    # roof rack:
    roof_rack = None
    poles = []
    modules = []

    solar_panels = []
    cargo_boxes = []
    big_cargo_boxes = []
    
    for obj in data_to.objects:
        if obj is not None:
            # bpy.context.scene.collection.objects.link(obj)
            vehicle_collection.objects.link(obj)
            if 'body' in obj.name.lower():
                body = obj
            elif 'wheel' in obj.name.lower():
                wheels.append(obj)
            elif 'spoiler' in obj.name.lower():
                spoiler = obj
            elif 'bullbar' in obj.name.lower():
                bullbar = obj
            elif 'roof-rack-pole' in obj.name.lower(): # to samo, co poniżej
                poles.append(obj)
            elif 'roof-rack' in obj.name.lower():
                roof_rack = obj
            elif 'solar-panel' in obj.name.lower():
                solar_panels.append(obj)
            elif 'big-cargo-box' in obj.name.lower(): # musi być przed cargo-box! bo "big-cargo-box" zawiera w sobie string "cargo-box"
                big_cargo_boxes.append(obj)
            elif 'cargo-box' in obj.name.lower():
                cargo_boxes.append(obj)

    if not (body and len(wheels)) == 4:
        return 1
    
    # bad names
    body.scale.x *= body_width
    body.scale.y *= body_length 
    body.scale.z *= body_height
    body.location.x += offset
    
    for wheel in wheels:
        wheel.scale.z *= wheel_thickness

    if is_red:
        mat = bpy.data.materials.new(name="RedMaterial")
        mat.diffuse_color = (0.8, 0.1, 0.1, 1)  # RGBA for red
        body.data.materials.append(mat)
    else:
        mat = bpy.data.materials.new(name="BlueMaterial")
        mat.diffuse_color = (0.2, 0.2, 0.7, 1)
        body.data.materials.append(mat)

    spoiler.hide_viewport = not has_spoiler
    bullbar.hide_viewport = not has_bullbar

    for i, pole in enumerate(poles):
        # pole.hide_viewport = not has_poles[i] == i #?
        pole.hide_viewport = not (i < has_poles)

    for i in range(3):
        solar_panels[i].hide_viewport = True
        cargo_boxes[i].hide_viewport = True
        big_cargo_boxes[i].hide_viewport = True

    for i, has_module in enumerate(has_modules):
        if has_module == "solar-panel":
            solar_panels[i].hide_viewport = False
        elif has_module == "cargo-box":
            cargo_boxes[i].hide_viewport = False
        elif has_module == "big-cargo-box":
            big_cargo_boxes[i].hide_viewport = False

    start_frame = frame
    end_frame = frame + view_vehicle_duration  # 2 seconds at 24 fps

    for obj in vehicle_collection.objects:
        # obj.hide_viewport = False
        obj.keyframe_insert(data_path="hide_viewport", frame=start_frame)
        
        obj.hide_viewport = True
        obj.keyframe_insert(data_path="hide_viewport", frame=end_frame)

        if frame != 0:
            obj.keyframe_insert(data_path="hide_viewport", frame=0)

def evaluate(genes):
    if not genes:
        return 1

    vehicle_type, body_width, body_height, body_length, wheel_thickness, is_red, has_spoiler, has_bullbar, \
         has_poles, has_modules = unpack_genes(genes)

    # aerodynamics score - prefer long and low cars. "Is red" and "has spoiler" are bonuses
    aero_score = (body_length / body_width) * (body_length / body_height) * 10 + \
        is_red * 5 + \
        has_spoiler * 5 - \
        has_bullbar * 5
    fuel_efficiency = -(body_width * body_height * body_length) + aero_score * 0.5
    weight = body_width * body_height * body_length + wheel_thickness + \
        10 if has_spoiler else 1 + \
        10 if has_bullbar else 1    
    friction_penalty = wheel_thickness * 10
    cargo_score = body_width * body_height * body_length
    offroad_score = wheel_thickness * 15 + has_bullbar * 10
    cost_penalty = has_spoiler * 10 + has_bullbar * 10
    
    pre_roof_score = 0
    if scenario == 'race':
        pre_roof_score = aero_score - friction_penalty
    elif scenario == 'cargo':
        pre_roof_score = cargo_score - cost_penalty
    elif scenario == 'offroad':
        pre_roof_score = offroad_score
    elif scenario == 'city':
        pre_roof_score = fuel_efficiency - weight - cost_penalty

    roof_score = 0
    for module in has_modules:
        if module == "solar-panel":
            roof_score += 10 if (scenario == "city" or scenario == "offroad") else -5
        elif module == "cargo-box":
            roof_score += 10 if (scenario == "cargo" or scenario == "offroad") else -5
        elif module == "big-cargo-box":
            roof_score += 15 if scenario == "cargo" else -10

    # dodatkowa nagroda za połączone duże skrzynie
    if has_modules == ["big-cargo-box", "big-cargo-box", "big-cargo-box"] and \
       scenario == "cargo":
        roof_score += 20
    elif has_modules[:-1] == ["big-cargo-box", "big-cargo-box"] or \
       has_modules[1:] == ["big-cargo-box", "big-cargo-box"] and \
       scenario == "cargo":
        roof_score += 10

    # penalize unused poles (extra weight without benefit) no matter the car type
    unused_poles = has_modules.count(None) - (3-has_poles)
    roof_score -= unused_poles * 5

    return pre_roof_score + roof_score

def create_random_genes():
    has_poles = random.randint(0, 3)
    has_modules = [
        random.choice(["solar-panel", "cargo-box", "big-cargo-box", None])
        for _ in range(has_poles)
    ]
    has_modules.extend([None] * (3 - has_poles))

    genes = {
        "binary": {
            "is_red": random.random() < 0.5,
            "has_spoiler": random.random() < 0.5,
            "has_bullbar": random.random() < 0.5
        },
        "continuous": {
            "body_width": random.uniform(0.75, 1.5),
            "body_height": random.uniform(0.75, 1.5),
            "body_length": random.uniform(0.75, 1.5),
            "wheel_thickness": random.uniform(0.75, 1.5)
        },
        "vehicle_type": random.choice(["GA-pickup", "GA-truck"]),
        "roof_rack": {
            "has_poles": has_poles,
            "has_modules": has_modules
        }
    }

    return genes

def mutate(genes):
    mutated_genes = genes.copy()
    
    if random.random() < mutation_rate:
        mutated_genes["vehicle_type"] = random.choice(["GA-pickup", "GA-truck"])
    for continuous_gene in mutated_genes["continuous"]:
        mutated_genes["continuous"][continuous_gene] += random.uniform(-0.15, 0.15)
        mutated_genes["continuous"][continuous_gene] = max(0.4, min(1.8, mutated_genes["continuous"][continuous_gene]))
    for binary_gene in mutated_genes["binary"]:
        if random.random() < mutation_rate:
            mutated_genes["binary"][binary_gene] = not mutated_genes["binary"][binary_gene]

    # roof rack mutations        
    mutated_genes["roof_rack"]["has_poles"] += random.randint(-1, 1)
    mutated_genes["roof_rack"]["has_poles"] = max(0, min(3, mutated_genes["roof_rack"]["has_poles"]))
    mutated_genes["roof_rack"]["has_modules"] = [random.choice(["solar-panel", "cargo-box", "big-cargo-box", None]) 
                                                 if random.random() < mutation_rate 
                                                 else module 
                                                 for module in mutated_genes["roof_rack"]["has_modules"][:mutated_genes["roof_rack"]["has_poles"]]
                                                 ] # po else chyba za malo
    # >>> A
    # [1, 2, 3]
    # >>> A[:4]
    # [1, 2, 3]
    while len(mutated_genes["roof_rack"]["has_modules"]) < 3:
        mutated_genes["roof_rack"]["has_modules"].append(None) #?
    
    return mutated_genes

def crossover(genes1, genes2):
    genes = { "binary": {}, "continuous": {}, "vehicle_type": 0, "roof_rack": { "has_poles": 0, "has_modules": [] } }
    for binary_gene in genes1["binary"]:
        genes["binary"][binary_gene] = random.choice([genes1["binary"][binary_gene], genes2["binary"][binary_gene]])
    for continuous_gene in genes1["continuous"]:
        genes["continuous"][continuous_gene] = random.choice([genes1["continuous"][continuous_gene], genes2["continuous"][continuous_gene]])
    genes["vehicle_type"] = random.choice([genes1["vehicle_type"], genes2["vehicle_type"]])
        
    # roof rack crossover
    genes["roof_rack"]["has_poles"] = random.choice([genes1["roof_rack"]["has_poles"], genes2["roof_rack"]["has_poles"]])

    valid_modules1 = genes1["roof_rack"]["has_modules"][:genes1["roof_rack"]["has_poles"]]
    valid_modules2 = genes2["roof_rack"]["has_modules"][:genes2["roof_rack"]["has_poles"]]

    for i in range(genes["roof_rack"]["has_poles"]):
        # obu rodziców ma moduł na danym miejscu
        if i < len(valid_modules1) and i < len(valid_modules2):
            module = random.choice([valid_modules1[i], valid_modules2[i]])
        # rodzic 1 ma moduł na danym miejscu
        elif i < len(valid_modules1):
            module = valid_modules1[i]
        # rodzic 2 ma moduł na danym miejscu
        elif i < len(valid_modules2):
            module = valid_modules2[i]
        # żaden rodzic nie ma modułu na danym miejscu
        else:
            module = None
        genes["roof_rack"]["has_modules"].append(module)

    return genes

def tournament_selection(population, tournament_size, n_parents):
    selected_parents = []
    for _ in range(n_parents):
        tournament = random.sample(population, tournament_size)
        winner = max(tournament, key=lambda x: x[0])
        selected_parents.append(winner)
    return selected_parents

def genetic_algorithm():
    population = [create_random_genes() for _ in range(population_size)]
    load_vehicle(population[0], 0) #, -5) # reference to see the progress
    best_vehicle = None

    for generation in range(generations):
        vehicles = []
        for genes in population:
            score = evaluate(genes)
            vehicles.append((score, genes))

        vehicles.sort(reverse=True, key=lambda x: x[0])
        best_score, best_genes = vehicles[0][0], vehicles[0][1]
        if best_vehicle is None or best_score > best_vehicle[0]:
            best_vehicle = (best_score, best_genes)
        print(f"Generation {generation + 1}: best score = {best_score}")

        if generation != 0:
            load_vehicle(best_genes, generation*view_vehicle_duration)

        parents = tournament_selection(vehicles, tournament_size, population_size)
        new_population = []
        for _ in range(population_size):
            parent1, parent2 = random.sample(parents, 2)
            child_genes = crossover(parent1[1], parent2[1])
            if random.random() < mutation_rate:
                child_genes = mutate(child_genes)
            new_population.append(child_genes)
        population = new_population

    load_vehicle(best_vehicle[1], generations*view_vehicle_duration) #, 5)
    print(f"Evolution complete - best score: {best_vehicle[0]}")

bpy.context.scene.frame_end = total_frames
clear_scene()
create_plane()
genetic_algorithm()