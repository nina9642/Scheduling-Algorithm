import random
import csv
import asyncio

def read_csv(file_path, skip_header=True):
    result = []
    with open(file_path, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        if skip_header:
            next(reader)
        for row in reader:
            result.append(row)
    return result
    
def str_to_int(t):
    t = t.split(':')
    if len(t) != 2:
        return None
    t = int(t[0])*60 + int(t[1])
    return t

def overlap(start1, end1, start2, end2):
    if start1 <= start2 <= end1 or start2 <= start1 <= end2:
        return True
    return False

def create_individual(availability):
    schedule = []
    ta_names = availability[0]
    for row in availability[1:]:
        l = []
        for i in range(1, len(row)):
            if row[i] == 1:
                l.append(ta_names[i])
        #print(l)
        rc = random.choice(l)
        #print('rc', rc)
        schedule.append((row[0], rc))
    return schedule #rows made up of lab, then a TA assigned to each in tuples

def fitness(labs, schedule):
    d = {}

    # Build dictionary: TA -> list of assigned labs
    for i in range(len(schedule)):
        ta = schedule[i][1]
        if ta not in d:
            d[ta] = []
        d[ta].append(i)

    # Count conflicts
    conflicts = 0

    for ta in d:
        assigned = d[ta]
        for i in range(len(assigned)):
            for j in range(i + 1, len(assigned)):
                lab1 = assigned[i]
                lab2 = assigned[j]

                if labs[lab1][1] == labs[lab2][1]:
                    if overlap(
                        labs[lab1][2], labs[lab1][3],
                        labs[lab2][2], labs[lab2][3]
                    ):
                        conflicts += 1

    # Count unused TAs and workload imbalance
    unused = 0
    dev = 0

    for ta in availability[0][1:]:
        actual = len(d.get(ta, []))

        if actual == 0:
            unused += 1

        dev += abs(mean - actual)

    # Higher is better
    return 1000 - 100 * conflicts - 50 * unused - dev  

def parent(P, TSIZE):
    v = random.sample(P, TSIZE)

    best = v[0]
    best_fit = fitness(labs, best)

    for individual in v:
        fit = fitness(labs, individual)

        if fit > best_fit:
            best = individual
            best_fit = fit

    return best

def crossover(parent1, parent2):
    child = []
    for i in range(lab_total):
        u = random.uniform(0,1)
        if u > 0.5:
            child.append(parent1[i])
        else:
            child.append(parent2[i])
    return child

def mutation(child):
    ta_names = availability[0]

    for i in range(len(child)):
        if random.random() < MUTATION_RATE:
            choices = [
                ta_names[j]
                for j in range(1, len(availability[i + 1]))
                if availability[i + 1][j] == 1]
            child[i] = (child[i][0], random.choice(choices))
    return child

def bestfitness(P):
    max_fit = fitness(labs, P[0])
    max_p = P[0]
    for p in P: 
        if fitness(labs, p) > max_fit:
            max_fit = fitness(labs, p)
            max_p = p
    return max_fit, max_p

file_path = 'Lab Schedule.csv'
file_path2 = 'Availability.csv'
labs = read_csv(file_path)                     # skip header
availability = read_csv(file_path2, False)
lab_total = len(labs) #this counts the number of rows in labs to know total
ta_total = len(availability[0]) - 1 #availability[0] is the first row minus "lab name"
mean = lab_total/ta_total # equal to 1.739
POPULATION_SIZE = 1500 #number of schedules in population
MUTATION_RATE = 0.1 #probability of mutation
GENERATIONS = 100 #max number of generations 
TSIZE = 5

lab_time_labels = {}
for row in labs:
    lab_time_labels[row[0]] = (row[2], row[3])
    row[1] = int(row[1])
    row[2] = str_to_int(row[2])
    row[3] = str_to_int(row[3])
    #print(row)

ta_names = availability[0][1:]

for row in availability[1:]:
    for i in range(1,len(row)):
        if row[i] == '':
            row[i] = 0
        else:
            row[i] = 1
    #print(row)

f = 0
w = []

async def run_solver_async():
    global P, f, w
    P = [create_individual(availability) for _ in range(POPULATION_SIZE)]
    for step in range(GENERATIONS):
        f, w = bestfitness(P)
        print(f'SOLVER_PROGRESS {step + 1}/{GENERATIONS}')
        P2 = []
        for i in range(POPULATION_SIZE):
            parent1 = parent(P, TSIZE)
            parent2 = parent(P, TSIZE)
            child = mutation(crossover(parent1, parent2))
            P2.append(child)
        P = P2
        await asyncio.sleep(0)
    return f, w

if __name__ == '__main__':
    asyncio.run(run_solver_async())
    from operator import itemgetter
    sorted_w = sorted(w, key=itemgetter(1))
    for row in sorted_w:
        print(row[0], row[1])
    print(f)

