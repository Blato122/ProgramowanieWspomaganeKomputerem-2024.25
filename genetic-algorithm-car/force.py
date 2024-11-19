import bpy
import random
import math

# GA hyperparameters
population_size = 10
generations = 10
mutation_rate = 0.2

# Fixed chassis volume
chassis_volume = 50  # Adjust as needed

# Utility functions
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_inclined_plane():
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0))
    ground = bpy.context.object
    ground.rotation_euler[0] = math.radians(-5)
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = 'PASSIVE'
    ground.rigid_body.friction = 0.5
    return ground

def create_vehicle(genes):
    chassis_width, chassis_height, wheel_radius, wheel_thickness, has_spoiler, is_red = genes
    
    # Calculate chassis_length based on fixed volume
    chassis_length = chassis_volume / (chassis_width * chassis_height)
    
    # Create chassis
    chassis_z = wheel_radius + chassis_height
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, chassis_z + 1))
    chassis = bpy.context.object
    chassis.scale = (chassis_width, chassis_length, chassis_height)
    
    # Mass proportional to volume (volume is constant, so mass is constant)
    volume = chassis_length * chassis_width * chassis_height
    chassis_mass = volume #** 2  # square the volume so that it's more visible in the simulation
    
    # Aerodynamic penalty: wider and higher vehicles are less aerodynamic
    # aerodynamic_penalty = (chassis_width + chassis_height)
    # chassis_mass /= aerodynamic_penalty
    
    # Add rigid body physics to chassis
    bpy.ops.rigidbody.object_add()
    chassis.rigid_body.type = 'ACTIVE'
    chassis.rigid_body.mass = chassis_mass
    chassis.rigid_body.friction = 0.5
    
    # After adding rigid body physics to the chassis in create_vehicle()
    chassis.rigid_body.linear_damping = (chassis_width + chassis_height) * 0.1  # Adjust the multiplier as needed
    # Set initial_motor_velocity, increase for red cars
    initial_motor_velocity = 1  # Base speed

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
        # chassis.rigid_body.mass *= 2
        chassis.rigid_body.linear_damping *= 0.5  # Reduce air resistance for cars with spoilers
        initial_motor_velocity += 1  # Increase speed for cars with spoilers

    # If 'is_red' is True, reduce linear damping and set the chassis material to red
    if is_red:
        chassis.rigid_body.linear_damping *= 0.5  # Reduce air resistance for red cars
        initial_motor_velocity += 1  # Increase speed for red cars

        # Create red material and assign it to the chassis
        mat = bpy.data.materials.new(name="RedMaterial")
        mat.diffuse_color = (1, 0, 0, 1)  # RGBA for red
        chassis.data.materials.append(mat)

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
            rotation=(0, math.radians(90), 0)
        )
        wheel = bpy.context.object
        
        # Add physics with friction proportional to thickness
        bpy.ops.rigidbody.object_add()
        wheel.rigid_body.type = 'ACTIVE'
        wheel.rigid_body.mass = 0.5
        wheel.rigid_body.friction = 1 + 1/(1-wheel_thickness)

        # Create hinge constraint
        # bpy.ops.object.empty_add(type='PLAIN_AXES', location=wheel.location)
        # constraint = bpy.context.object
        
        # bpy.ops.rigidbody.constraint_add()
        # constraint.rigid_body_constraint.type = 'HINGE'
        # constraint.rigid_body_constraint.object1 = chassis
        # constraint.rigid_body_constraint.object2 = wheel
        # constraint.rotation_euler = (0, math.radians(90), 0)

        # Create an empty object to act as the constraint pivot
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=wheel.location)
        constraint_empty = bpy.context.object
        constraint_empty.rotation_euler = (0, 0, 0)  # Ensure correct rotation

        # Add a hinge constraint between the chassis and the wheel
        bpy.ops.rigidbody.constraint_add()
        constraint = constraint_empty
        constraint.rigid_body_constraint.type = 'HINGE'
        constraint.rigid_body_constraint.object1 = chassis
        constraint.rigid_body_constraint.object2 = wheel

        # Enable motor in the hinge constraint
        # constraint.rigid_body_constraint.use_motor = True
        constraint.rigid_body_constraint.motor_ang_target_velocity = initial_motor_velocity
        constraint.rigid_body_constraint.motor_ang_max_impulse = 100  # Adjust as needed

        # Set the hinge axis (assumes wheels rotate around local X-axis)
        constraint.rigid_body_constraint.axis_x = True
        constraint.rigid_body_constraint.axis_y = False
        constraint.rigid_body_constraint.axis_z = False

    return chassis

def evaluate(vehicle):
    # Set simulation frame range
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 24 * 3  # Adjust as needed

    # Run the simulation
    bpy.ops.screen.frame_jump(end=False)
    bpy.ops.screen.animation_play()

    # Let the simulation run for all frames
    for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()

    bpy.ops.screen.animation_cancel()

    # Get the vehicle's final Y position as fitness
    final_distance = vehicle.matrix_world.translation[1]

    print(vehicle.matrix_world.translation)
    return final_distance

def create_random_genes():
    # Randomly generate chassis_width and chassis_height
    chassis_width = random.uniform(2, 4)
    chassis_height = random.uniform(2, 4)
    
    # Other genes
    wheel_radius = random.uniform(0.2, 0.5)
    wheel_thickness = random.uniform(0.05, 0.95)
    has_spoiler = random.choice([True, False])

    is_red = random.choice([True, False])

    return [
        chassis_width,
        chassis_height,
        wheel_radius,
        wheel_thickness,
        has_spoiler,
        is_red
    ]

def mutate(genes):
    mutated_genes = genes.copy()
    # Mutate chassis_width and chassis_height
    mutated_genes[0] += random.uniform(-0.2, 0.2)  # chassis_width
    mutated_genes[1] += random.uniform(-0.2, 0.2)  # chassis_height

    # Ensure dimensions are positive
    mutated_genes[0] = max(0.1, mutated_genes[0])
    mutated_genes[1] = max(0.1, mutated_genes[1])

    # Mutate other genes
    mutated_genes[2] += random.uniform(-0.1, 0.1)  # wheel_radius
    mutated_genes[3] += random.uniform(-0.1, 0.1)  # wheel_thickness
    mutated_genes[2] = max(0.1, mutated_genes[2])  # Ensure positive
    mutated_genes[3] = max(0.01, mutated_genes[3])  # Ensure positive

    # binary features (spoiler and is_red)
    mutated_genes[4] = mutated_genes[4] if random.random() < 0.9 else not mutated_genes[4]
    mutated_genes[5] = mutated_genes[5] if random.random() < 0.9 else not mutated_genes[5]

    return mutated_genes

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
    print(f"Best score: {best[0]}")

# Run the genetic algorithm
genetic_algorithm()