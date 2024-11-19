import bpy
import random
import math

# GA hyperparameters
population_size = 5
generations = 5
mutation_rate = 0.2

# fixed chassis volume - modify the dimensions instead (more or less aero)
chassis_volume = 50

# utility functions
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

# add road texture
def create_plane():
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0))

# Add at the beginning with other constants
CAR_TYPES = ['sedan', 'pickup', 'hatchback', 'combi']

def create_pickup(genes):
    chassis_width, chassis_height, wheel_radius, wheel_thickness, has_spoiler, is_red, _ = genes
    chassis_length = chassis_volume / (chassis_width * chassis_height)
    chassis_z = wheel_radius #+ 
    
    # Create main cabin
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, chassis_z))
    cabin = bpy.context.object
    cabin.scale = (chassis_width, chassis_length/3, chassis_height)
    
    # Create truck bed
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, chassis_z))
    bed = bpy.context.object
    bed.scale = (chassis_width, 2*chassis_length/3, chassis_height/2)
    bed.parent = cabin
    
    # Create bed walls
    wall_thickness = 0.1
    for x in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x * chassis_width/2, 0, chassis_z))
        wall = bpy.context.object
        wall.scale = (wall_thickness, chassis_length/2, chassis_height/4)
        wall.parent = cabin
    
    # # Create front grille
    # bpy.ops.mesh.primitive_cube_add(size=1, location=(0, chassis_length/2 + 0.1, chassis_z - chassis_height/4))
    # grille = bpy.context.object
    # grille.scale = (chassis_width * 0.8, 0.1, chassis_height/2)
    # grille.parent = cabin
    
    # # Create hood
    # bpy.ops.mesh.primitive_cube_add(size=1, location=(0, chassis_length/2.5, chassis_z))
    # hood = bpy.context.object
    # hood.scale = (chassis_width, chassis_length/4, 0.1)
    # hood.parent = cabin
    
    # Add color
    if is_red:
        mat = bpy.data.materials.new(name="RedMaterial")
        mat.diffuse_color = (1, 0, 0, 1)
        for obj in [cabin, bed]:#, grille, hood]:
            obj.data.materials.append(mat)
    
    # Add spoiler if needed
    if has_spoiler:
        spoiler_height = chassis_height * 0.1
        spoiler_length = chassis_length * 0.1
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(0, chassis_length/2, chassis_z + chassis_height/2)
        )
        spoiler = bpy.context.object
        spoiler.scale = (chassis_width, spoiler_length, spoiler_height)
        spoiler.parent = cabin
    
    # Add wheels
    wheel_positions = [
        (chassis_width/2, chassis_length/2, wheel_radius),
        (-chassis_width/2, chassis_length/2, wheel_radius),
        (chassis_width/2, -chassis_length/2, wheel_radius),
        (-chassis_width/2, -chassis_length/2, wheel_radius),
    ]
    
    for pos in wheel_positions:
        x, y, z = pos
        create_wheel(x, y, z, wheel_radius, wheel_thickness, cabin)
    
    return cabin

def create_wheel(x, y, z, radius, thickness, parent):
    # Create wheel mesh with proper rotation
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=thickness,
        location=(x, y, z),
        rotation=(math.radians(90), 0, 0)  # Changed rotation order
    )
    wheel = bpy.context.object
    wheel.parent = parent
    
    # Add black material for wheels
    mat = bpy.data.materials.new(name="WheelMaterial")
    mat.diffuse_color = (0.1, 0.1, 0.1, 1)  # Dark gray/black
    wheel.data.materials.append(mat)
    
    return wheel

def create_vehicle(genes):
    # car_type = genes[6]
    # if car_type == 'pickup':
        return create_pickup(genes)
    # Add similar detailed functions for other car types
    # else:
    #     # Default to simple sedan
    #     return create_simple_vehicle(genes)

def evaluate(vehicle):
    genes = vehicle.get("genes", None)
    if not genes:
        return 0 # TU ZAWSZE BEDZIE WCHODZIC CHYBA!!!
    
    chassis_width, chassis_height, _, wheel_thickness, has_spoiler, is_red, _ = genes
    chassis_length = chassis_volume / (chassis_width * chassis_height)
    
    # Aerodynamics score - prefer long and low cars
    aero_score = (chassis_length / chassis_width) * (chassis_length / chassis_height) * 10
    
    # Spoiler bonus
    spoiler_bonus = 15 if has_spoiler else 0
    
    # Color bonus
    color_bonus = 10 if is_red else 0
    
    # Wheel friction penalty
    friction_penalty = wheel_thickness * 20 # 1 to 19
    
    return aero_score + spoiler_bonus + color_bonus - friction_penalty

def create_random_genes():
    chassis_width = random.uniform(2, 4)
    chassis_height = random.uniform(2, 4)
    wheel_radius = random.uniform(0.2, 0.5)
    wheel_thickness = random.uniform(0.05, 0.95)
    has_spoiler = random.choice([True, False])
    is_red = random.choice([True, False])
    car_type = random.choice(CAR_TYPES)
    
    return [
        chassis_width,
        chassis_height,
        wheel_radius,
        wheel_thickness,
        has_spoiler,
        is_red,
        car_type
    ]

def mutate(genes):
    mutated_genes = genes.copy()
    
    # Mutate numeric values
    mutated_genes[0] += random.uniform(-0.2, 0.2)  # chassis_width
    mutated_genes[1] += random.uniform(-0.2, 0.2)  # chassis_height
    mutated_genes[2] += random.uniform(-0.1, 0.1)  # wheel_radius
    mutated_genes[3] += random.uniform(-0.1, 0.1)  # wheel_thickness
    
    # Ensure positive values
    mutated_genes[0] = max(0.1, mutated_genes[0])
    mutated_genes[1] = max(0.1, mutated_genes[1])
    mutated_genes[2] = max(0.1, mutated_genes[2])
    mutated_genes[3] = max(0.01, mutated_genes[3])
    
    # Mutate boolean values
    if random.random() < mutation_rate:
        mutated_genes[4] = not mutated_genes[4]  # has_spoiler
    if random.random() < mutation_rate:
        mutated_genes[5] = not mutated_genes[5]  # is_red
    
    # Mutate car type
    if random.random() < mutation_rate:
        mutated_genes[6] = random.choice(CAR_TYPES)
    
    return mutated_genes

def crossover(genes1, genes2):
    return [random.choice([genes1[i], genes2[i]]) for i in range(len(genes1))]

def genetic_algorithm():
    population = [create_random_genes() for _ in range(population_size)]
    best = None

    for generation in range(generations):
        fitness_scores = []
        for genes in population:
            vehicle = create_vehicle(genes)
            score = evaluate(vehicle)
            fitness_scores.append((score, genes))

        fitness_scores.sort(reverse=True, key=lambda x: x[0])
        best_genes = fitness_scores[0][1]
        best_score = fitness_scores[0][0]
        if best is None or best_score > best[0] and best_score < 100:
            best = (best_score, best_genes)
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
    create_vehicle(best[1])
    print("Evolution complete. Best vehicle created.")
    print(f"Best score: {best[0]}")

# Run the genetic algorithm
genetic_algorithm()