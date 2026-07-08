import random

def create_schedule():
    return[(random.randint(0,NUM_WORKERS - 1), random.randint(0,NUM_SLOTS - 1)) for _ in range(NUM_TASKS)]

def fitness(schedule):
    conflicts = 0
    total_priority = 0
    worker_load = [[0] * NUM_SLOTS for _ in range(NUM_WORKERS)]

    for task_index, (worker, slot) in enumerate(schedule):
        worker_load[worker][slot] += 1
        total_priority += TASK_PRIORITIES[task_index]

    for worker in range(NUM_WORKERS):
        for slot in range(NUM_SLOTS):
            if worker_load[worker][slot] > 1:
                conflicts += worker_load[worker][slot] -1
    
    return total_priority - 5 * conflicts

def parent(P, TSIZE):
    v = random.sample(P, TSIZE)
    max_fit = fitness(v[0])
    max_i = v[0]
    for i in range(TSIZE):
        if fitness(v[i]) > max_fit:
            max_fit = fitness(v[i])
            max_i = v[i]
    return max_i 

def crossover(parent1, parent2):
    child = []
    for i in range(NUM_TASKS):
        u = random.uniform(0,1)
        if u > 0.5:
            child.append(parent1[i])
        else:
            child.append(parent2[i])
    return child

def mutation(child):
    return create_schedule() if random.random() < MUTATION_RATE else child

NUM_WORKERS = 3 #workers W1, W2, W3
NUM_TASKS = 5 #tasks T1, T2, etc
NUM_SLOTS = 4 #time slots
POPULATION_SIZE = 50 #number of schedules in population
MUTATION_RATE = 0.1 #probability of mutation
GENERATIONS = 100 #max number of generations 
TASK_PRIORITIES = [1,2,1,3,2] #priority weights for tasks 
P = [create_schedule() for _ in range(POPULATION_SIZE)]
TSIZE = 3
MAX_FITNESS = 9

for step in range(GENERATIONS):
    f = mutation(crossover(parent(P, TSIZE),parent(P, TSIZE)))
    print(f,fitness(f))
    if fitness(f) == MAX_FITNESS:
        break
    P2 = []
    for i in range(POPULATION_SIZE):
        parent1 = parent(P, TSIZE)
        parent2 = parent(P, TSIZE)
        P2.append(mutation(crossover(parent1, parent2)))
    P = P2

#print(mutation(crossover(parent(P, TSIZE), parent(P, TSIZE))))
#print(fitness(create_schedule()))
