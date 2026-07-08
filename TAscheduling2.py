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
    for i in range(len(schedule)):
        TA = schedule[i][1] #assigned schedule[i][1] to a common variable 
        if TA not in d: #if the TA wasn't already in the dictionary as a key, add it
            d[TA] = [i]
        else:
            d[TA].append(i) #otherwise, append the value into the existing key
    # total = 0 all of this tested to make sure that tht etotal lab # was 40
    # l = []
    # for k in d:
    #     total += len(d[k])
    #     l += d[k]
    for k in d: #for key in dictionary
        assigned = d[k] #this is the list of values for the given key
        for i in assigned: #nested loop
            for j in assigned: #i and j run through the same code
                if i != j: #so if they're not equal, test for overlap
                    start1 = labs[i][2]
                    end1 = labs[i][3]
                    start2 = labs[j][2]
                    end2 = labs[j][3]
                    if overlap(start1, end1, start2, end2):
                        return 0 #low fitness function = unfit
        dev = 0
        for k in d:
            actual = len(d[k]) #actual length of value for key in dict
            dev += (mean - actual)*(mean - actual) 
            #print(actual, dev)
        dev += (ta_total - len(d)) * (mean * mean)

        # to make sure everyone is assigned something
        return ta_total/(dev)
        #ta_total bc finds average among the number - inconsistent if diff # of ppl       

def parent(P, TSIZE):
    v = random.sample(P, TSIZE)
    max_fit = fitness(labs,v[0])
    max_i = v[0]
    for i in range(TSIZE):
        if fitness(labs,v[i]) > max_fit:
            max_fit = fitness(labs,v[i])
            max_i = v[i]
    return max_i 

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
for row in labs:
    row[1] = int(row[1])
    row[2] = str_to_int(row[2])
    row[3] = str_to_int(row[3])

availability = read_csv_to_2d_list(file_path2)
for row in availability:
    for i in range(1,len(row)):
        if row[i] == '':
            row[i] = 0
        else:
            row[i] = 1

lab_total = len(labs) #this counts the number of rows in labs to know total
ta_total = len(availability[0]) - 1 #availability[0] is the first row minus "lab name"
mean = lab_total/ta_total # equal to 1.739
POPULATION_SIZE = 1500 #number of schedules in population
MUTATION_RATE = 0.01 #probability of mutation
GENERATIONS = 1000 #max number of generations 
TSIZE = 5

P = [create_individual(availability) for _ in range(POPULATION_SIZE)]

f1 = bestfitness(P)[0] - 1
for step in range(GENERATIONS):
    #f = mutation(crossover(parent(P, TSIZE), parent(P, TSIZE)))
    f,w = bestfitness(P) #if two things are being returned, format like this to assign the things
    if step % 100 == 0:
        print(step)
        if f - f1 < 0.00000000000001:
            print(step)
            break
        f1 = f
    #print('THIS IS STEP', step)
    #print(w)
    P2 = []
    for i in range(POPULATION_SIZE):
        parent1 = parent(P, TSIZE)
        parent2 = parent(P, TSIZE)
        P2.append(mutation(crossover(parent1, parent2)))
    P = P2
from operator import itemgetter
sorted_w = sorted(w, key=itemgetter(1))
for row in sorted_w:
    print(row[0], row[1])
print(f)

#print(availability)