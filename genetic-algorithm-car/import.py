import bpy
import random
import math

# GA hyperparameters
population_size = 5
generations = 5
mutation_rate = 0.2
scenario = 'cargo'

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_plane():
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, -3))
    plane = bpy.context.active_object
    
    # Create material
    mat = bpy.data.materials.new(name="Ground")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    # Add nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_image = nodes.new('ShaderNodeTexImage')
    
    # Load image texture
    tex_image.image = bpy.data.images.load("C:\\Users\\Admin\\Downloads\\asphalt-texture.jpg")

    # Set metallic and roughness
    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 1.0
    
    # Link nodes
    links.new(tex_coord.outputs['UV'], tex_image.inputs['Vector'])
    links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # Assign material to plane
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
        genes["binary"]["has_bullbar"]
    )

def scale_component(obj, body, scale_factor_x, scale_factor_y, scale_factor_z):
    offset_x = obj.location.x - body.location.x
    offset_y = obj.location.y - body.location.y
    offset_z = obj.location.z - body.location.z
    # Apply scaled offsets from body center
    obj.location.x = body.location.x + (offset_x * scale_factor_x)
    obj.location.y = body.location.y + (offset_y * scale_factor_y)
    obj.location.z = body.location.z + (offset_z * scale_factor_z)
    return obj

def load_vehicle(genes):
    vehicle_type, body_width, body_height, body_length, wheel_thickness, is_red, has_spoiler, has_bullbar = unpack_genes(genes)
    filepath = f"C:\\Users\\Admin\\Desktop\\{vehicle_type}.blend"
        
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = [name for name in data_from.objects]
    
    body = None
    wheels = []
    spoiler = None
    bullbar = None
    
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.scene.collection.objects.link(obj)
            if 'body' in obj.name.lower():
                body = obj
            elif 'wheel' in obj.name.lower():
                wheels.append(obj)
            elif 'spoiler' in obj.name.lower():
                spoiler = obj
            elif 'bullbar' in obj.name.lower():
                bullbar = obj
    
    if not (body and len(wheels)) == 4:
        return 1
    
    # Store initial wheel offsets from body center
    # initial_body_dimensions = (
    #     body.scale.x,
    #     body.scale.y,
    #     body.scale.z
    # )
    scale_factor_x = body_width
    scale_factor_y = body_length
    scale_factor_z = body_height
    body.scale.x *= scale_factor_x
    body.scale.y *= scale_factor_y 
    body.scale.z *= scale_factor_z
    
    # Update wheel positions using scaled offsets
    for wheel in wheels:
        # wheel_scale_y_initial = wheel.scale.y
        wheel.location.y *= wheel_thickness
        wheel = scale_component(wheel, body, scale_factor_x, scale_factor_y, scale_factor_z)
        # Modify wheel thickness while maintaining radius
        #wheel.scale.z *= wheel_thickness

    
    if is_red:
        # Create red material and assign it to the chassis
        mat = bpy.data.materials.new(name="RedMaterial")
        mat.diffuse_color = (1, 0, 0, 1)  # RGBA for red
        body.data.materials.append(mat)
    else:
        # Create blue material and assign it to the chassis
        mat = bpy.data.materials.new(name="BlueMaterial")
        mat.diffuse_color = (0, 0, 1, 1)
        body.data.materials.append(mat)

    if has_spoiler:
        spoiler = scale_component(spoiler, body, scale_factor_x, scale_factor_y, scale_factor_z)
    spoiler.hide_viewport = has_spoiler

    if has_bullbar:
        bullbar = scale_component(bullbar, body, scale_factor_x, scale_factor_y, scale_factor_z)
    bullbar.hide_viewport = has_bullbar

    body["genes"] = genes
    return body

def evaluate(vehicle):
    if not vehicle:
        return 1
    
    genes = vehicle.get("genes", None)
    if not genes:
        return 2
    
    vehicle_type, body_width, body_height, body_length, wheel_thickness, is_red, has_spoiler, has_bullbar = unpack_genes(genes)

    # Aerodynamics score - prefer long and low cars. "Is red" and "has spoiler" are bonuses
    aero_score = (body_length / body_width) * (body_length / body_height) * 10 + \
        is_red * 5 + \
        has_spoiler * 5
    fuel_efficiency = -(body_width * body_height * body_length) + aero_score * 0.5
    weight = body_width * body_height * body_length + wheel_thickness + \
        10 if has_spoiler else 1 + \
        10 if has_bullbar else 1    
    friction_penalty = wheel_thickness * 10
    cargo_score = body_width * body_height * body_length
    offroad_score = wheel_thickness * 15 + has_bullbar * 10
    cost_penalty = has_spoiler * 10 + has_bullbar * 10
    # ground clearance moze fr
    # moze safety tez
    
    if scenario == 'race':
        return aero_score - friction_penalty
    elif scenario == 'cargo':
        return cargo_score - cost_penalty
    elif scenario == 'offroad':
        return offroad_score - cost_penalty
    elif scenario == 'city':
        return fuel_efficiency - weight - cost_penalty

def create_random_genes():
    return {
        "binary": {
            "is_red": random.random() < 0.5,
            "has_spoiler": random.random() < 0.5,
            "has_bullbar": random.random() < 0.5
        },
        "continuous": {
            "body_width": random.uniform(0.8, 1.2),
            "body_height": random.uniform(0.8, 1.2),
            "body_length": random.uniform(0.8, 1.2),
            "wheel_thickness": random.uniform(0.8, 1.2)
        },
        "vehicle_type": random.choice(["GA-pickup", "GA-truck"]),
    }

def mutate(genes):
    mutated_genes = genes.copy()
    
    if random.random() < mutation_rate:
        mutated_genes["vehicle_type"] = random.choice(["GA-pickup", "GA-truck"])
    for continuous_gene in mutated_genes["continuous"]:
        mutated_genes["continuous"][continuous_gene] += random.uniform(-0.1, 0.1)
        mutated_genes["continuous"][continuous_gene] = max(0.5, min(1.5, mutated_genes["continuous"][continuous_gene]))
    for binary_gene in mutated_genes["binary"]:
        if random.random() < mutation_rate:
            mutated_genes["binary"][binary_gene] = not mutated_genes["binary"][binary_gene]
    
    return mutated_genes

def crossover(genes1, genes2):
    genes = { "binary": {}, "continuous": {}, "vehicle_type": 0 }
    for binary_gene in genes1["binary"]:
        genes["binary"][binary_gene] = random.choice([genes1["binary"][binary_gene], genes2["binary"][binary_gene]])
    for continuous_gene in genes1["continuous"]:
        genes["continuous"][continuous_gene] = random.choice([genes1["continuous"][continuous_gene], genes2["continuous"][continuous_gene]])
    genes["vehicle_type"] = random.choice([genes1["vehicle_type"], genes2["vehicle_type"]])
    return genes

def genetic_algorithm():
    population = [create_random_genes() for _ in range(population_size)]
    best_vehicle = None

    for generation in range(generations):
        fitness_scores = []
        for genes in population:
            clear_scene()
            create_plane()
            vehicle = load_vehicle(genes)
            score = evaluate(vehicle)
            fitness_scores.append((score, genes))

        fitness_scores.sort(reverse=True, key=lambda x: x[0])
        best_genes = fitness_scores[0][1]
        best_score = fitness_scores[0][0]
        if best_vehicle is None or best_score > best_vehicle[0]:
            best_vehicle = (best_score, best_genes)
        print(f"Generation {generation + 1}: best score = {fitness_scores[0][0]}")

        parents = fitness_scores[:population_size // 2]
        new_population = []
        for _ in range(population_size):
            parent1, parent2 = random.sample(parents, 2)
            child_genes = crossover(parent1[1], parent2[1])
            if random.random() < mutation_rate:
                child_genes = mutate(child_genes)
            new_population.append(child_genes)
        population = new_population

    clear_scene()
    create_plane()
    load_vehicle(best_vehicle[1])
    print("Evolution complete. Best vehicle created.")
    print(f"Best score: {best_vehicle[0]}")

# Run the genetic algorithm
genetic_algorithm()