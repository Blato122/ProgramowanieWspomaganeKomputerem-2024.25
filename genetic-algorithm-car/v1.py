import bpy
import random
import numpy as np

# frame related stuff
frame_duration = 12 # 24 fps?
total_steps = 100 # number of steps to simulate
frame_start = 1
frame_end = frame_start + total_steps * frame_duration - 1

# genetic algorithm stuff
population_size = 100
generations = 100
mutation_rate = 0.01
crossover_rate = 0.7

def evalutate(ind): # individual -> a vehicle
    pass

# aero?!?! maybe

class Vehicle:
    def __init__(self):
        self.wheels = None
        self.body = None
        self.color = None
        

vehicle = Vehicle()

# tych obiektów ma być cała populacja
# i no nie wiem, wszystkie UKRYTE czy coś?
# oprócz jednego, obecnie najlepszego
# i pokazywać nowego najlepszego co jedną klatkę? (czyli 12 bo frame duration)

for step in range(total_steps):
    frame = frame_start + step * frame_duration
    bpy.context.scene.frame_set(frame)
    vehicle.update(frame)
    vehicle.step()

bpy.context.scene.frame_end = frame_end