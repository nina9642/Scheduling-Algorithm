import random
import csv

def read_csv_to_2d_list(file_path):
    result = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip the first row (header)
            for row in csv_reader:
                result.append(row)
        return result
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return []
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []
    
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
    for row in availability:
        l = []
        for i in range(1, len(row)):
            if row[i] == 1:
                l.append(i)
        #print(l)
        rc = random.choice(l)
        #print('rc', rc)
        #print(l)
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

    for ta in range(1, ta_total + 1):
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
    for i in range(len(child)):
        if random.random() < MUTATION_RATE:
            l = [a for a in range(len(availability[i])) if availability[i][a] == 1]
            rc = random.choice(l)
            child[i] = (child[i][0],rc)
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
labs = read_csv_to_2d_list(file_path)
availability = read_csv_to_2d_list(file_path2)
lab_total = len(labs) #this counts the number of rows in labs to know total
ta_total = len(availability[0]) - 1 #availability[0] is the first row minus "lab name"
mean = lab_total/ta_total # equal to 1.739
POPULATION_SIZE = 1500 #number of schedules in population
MUTATION_RATE = 0.1 #probability of mutation
GENERATIONS = 100 #max number of generations 
TSIZE = 5

for row in labs:
    row[1] = int(row[1])
    row[2] = str_to_int(row[2])
    row[3] = str_to_int(row[3])
    #print(row)

for row in availability:
    for i in range(1,len(row)):
        if row[i] == '':
            row[i] = 0
        else:
            row[i] = 1
    #print(row)

P = [create_individual(availability) for _ in range(POPULATION_SIZE)]
print("Population size:", len(P))

for i in range(5):
    print(fitness(labs, P[i]))

f1 = 0
for step in range(GENERATIONS):
    #f = mutation(crossover(parent(P, TSIZE), parent(P, TSIZE)))
    f,w = bestfitness(P) #if two things are being returned, format like this to assign the things
    # if step % 100 == 0:
    #     print(step)
    #     if f - f1 < 0.00000000000001:
    #         print(step+1)
    #         break
    #     f1 = f
    print('THIS IS STEP', step)

    #print(w)
    P2 = []

    for i in range(POPULATION_SIZE):
        parent1 = parent(P, TSIZE)
        parent2 = parent(P, TSIZE)

        child = mutation(crossover(parent1, parent2))
        P2.append(child)

    P = P2
from operator import itemgetter
sorted_w = sorted(w, key=itemgetter(1))
for row in sorted_w:
    print(row[0], row[1])
print(f)
#print(availability)