import bpy
import random
import math

# GA hyperparameters
population_size = 100
generations = 10
mutation_rate = 0.2

# class Vehicle:

# utility function
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

# utility function
def create_inclined_plane():
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0))
    ground = bpy.context.object
    ground.rotation_euler[0] = math.radians(-5)
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = 'PASSIVE'
    ground.rigid_body.friction = 0.5
    return ground

def calculate_volume(length, width, height):
    return length * width * height

def create_vehicle(genes):
    chassis_length, chassis_height, chassis_width, wheel_radius, wheel_thickness, has_spoiler = genes
    
    # Create chassis
    chassis_z = wheel_radius + chassis_height
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, chassis_z + 1))
    chassis = bpy.context.object
    chassis.scale = (chassis_width, chassis_length, chassis_height)
    
    # Calculate mass based on volume
    volume = calculate_volume(chassis_length, chassis_width, chassis_height)
    chassis_mass = volume ** 2 # square the volume so that it's more visible in the simulation
    
    # Add rigid body physics to chassis
    bpy.ops.rigidbody.object_add()
    chassis.rigid_body.type = 'ACTIVE'
    chassis.rigid_body.mass = chassis_mass
    chassis.rigid_body.friction = 0.5

    # Aerodynamic effect: narrower body = less drag, shorter body = less drag
    chassis.rigid_body.mass /= chassis_width*5
    chassis.rigid_body.mass /= chassis_height*5

    # Add spoiler if gene indicates
    if has_spoiler:
        spoiler_height = chassis_height * 0.25
        spoiler_length = chassis_length * 0.25
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(0, -chassis_length/2, chassis_z + chassis_height/2)
        )
        spoiler = bpy.context.object
        spoiler.scale = (chassis_width, spoiler_length, spoiler_height)
        
        # Parent spoiler to chassis
        spoiler.parent = chassis
        
        # Apply downforce effect by increasing mass slightly
        chassis.rigid_body.mass *= 2

    # Update wheel creation with friction based on thickness
    wheel_positions = [
        (chassis_width/2, chassis_length/2, wheel_radius + 1),
        (-chassis_width/2, chassis_length/2, wheel_radius + 1),
        (chassis_width/2, -chassis_length/2, wheel_radius + 1),
        (-chassis_width/2, -chassis_length/2, wheel_radius + 1),
    ]

    for pos in wheel_positions:
        x, y, z = pos
        bpy.ops.mesh.primitive_cylinder_add(
            radius=wheel_radius,
            depth=wheel_thickness,
            location=(x, y, z),
            rotation=(0, math.radians(90), 0)  # Changed rotation to fix upward movement
        )
        wheel = bpy.context.object
        
        # Add physics with friction proportional to thickness
        bpy.ops.rigidbody.object_add()
        wheel.rigid_body.type = 'ACTIVE'
        wheel.rigid_body.mass = 0.5
        wheel.rigid_body.friction = 0.5 + 10/(1-wheel_thickness)  # More thickness = more friction

        # Create hinge constraint with corrected orientation
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=wheel.location)
        constraint = bpy.context.object
        
        bpy.ops.rigidbody.constraint_add()
        constraint.rigid_body_constraint.type = 'HINGE'
        constraint.rigid_body_constraint.object1 = chassis
        constraint.rigid_body_constraint.object2 = wheel
        constraint.rotation_euler = (0, math.radians(90), 0)

    return chassis

def evaluate(vehicle):
    # Set simulation frame range
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 24 * 5  # Adjust as needed

    # Run the simulation
    bpy.ops.screen.frame_jump(end=False)
    bpy.ops.screen.animation_play()

    # Let the simulation run for all frames
    for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()

    bpy.ops.screen.animation_cancel()

    # Get the vehicle's final X position as fitness
    final_distance = vehicle.matrix_world.translation[1]

    print(vehicle.matrix_world.translation)
    return final_distance

def create_random_genes():
    return [
        random.uniform(2, 5),     # chassis_length
        random.uniform(2, 5), # chassis_height
        random.uniform(2, 5),   # chassis_width
        random.uniform(0.2, 0.5), # wheel_radius
        random.uniform(0.05, 0.95), # wheel_thickness
        random.choice([True, False]), # has_spoiler
        # random.choice([True, False]), # has slanted front
        # random.choice([True, False]) # is red (hehe)
    ]

def mutate(genes):
    return [
        genes[0] + random.uniform(-0.2, 0.2),  # chassis_length
        genes[1] + random.uniform(-0.2, 0.2),  # chassis_height
        genes[2] + random.uniform(-0.2, 0.2),  # chassis_width
        genes[3] + random.uniform(-0.1, 0.1),  # wheel_radius
        genes[4] + random.uniform(-0.1, 0.1),  # wheel_thickness
        genes[5]  # has_spoiler remains unchanged
    ]

def crossover(genes1, genes2):
    return [random.choice([genes1[i], genes2[i]]) for i in range(len(genes1))]

def genetic_algorithm():
    population = [create_random_genes() for _ in range(population_size)]
    best = None

    for generation in range(generations):
        fitness_scores = []
        for genes in population:
            clear_scene()
            create_inclined_plane()
            vehicle = create_vehicle(genes)
            score = evaluate(vehicle)
            fitness_scores.append((score, genes))

        fitness_scores.sort(reverse=True, key=lambda x: x[0])
        best_genes = fitness_scores[0][1]
        best_score = fitness_scores[0][0]
        if best is None or best_score > best[0] and best_score < 100:
            best = (best_score, best_genes)
        print(f"Generation {generation + 1}: Best Score = {fitness_scores[0][0]}")
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
    create_inclined_plane()
    create_vehicle(best[1])
    print("Evolution complete. Best vehicle created in the final frame.")
    print(best[0])

# Run the genetic algorithm
genetic_algorithm()