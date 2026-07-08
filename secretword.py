import random
import string

def individual(LENGTH):
    return ''.join(random.choice(string.ascii_uppercase + ' ') for x in range(LENGTH))

def fitness(str):
    correct = 0 
    for a in range(len(str)):
        if str[a] == SECRET[a]:
            correct += 1
    return correct

def parent(P, TSIZE):
    v = random.sample(P, TSIZE)
    max_fit = fitness(P[0]) #this was initially -1, but it's better to not do that bc what if -1's in range
    max_i = v[0] #forgot to initialize this variable--must assign for all variables
    for i in range(TSIZE):
        #print(fitness(v[i]), v[i])
        if fitness(v[i]) > max_fit:
            max_fit = fitness(v[i])
            max_i = v[i]
    return max_i

def crossover(parent1, parent2):
    x = random.randint(0,len(SECRET)-1) #this chooses a random number which is used below to index 
    child = parent1[:x] + parent2[x:] #this is how you join two strings using slices
    return child 

def mutation(child):
    return ''.join(random.choice(string.ascii_uppercase + ' ') 
                   if random.random() < MUTATION_RATE else c for c in child)

def bestfitness(P):
    max_fit = fitness(P[0])
    max_p = P[0]
    for p in P: #important to remember how to find the max number in a list without sorting (sorting's long)
        if fitness(p) > max_fit:
            max_fit = fitness(p)
            max_p = p
    return max_fit, max_p

SECRET = "HI IM NINA"
SIZE = 100 #constants should all be all caps 
MAX_STEPS = 1000
LENGTH = len(SECRET) #don't hard code the length of the word, instead use len()
MUTATION_RATE = 0.01 #random.random chooses a number from 0 to 1. 
#this means that if the number's less than 0.01, it will mutate, simulating a 1% chance
TSIZE = 3
P = [individual(LENGTH) for _ in range(SIZE)]

for step in range(MAX_STEPS):
    f,w = bestfitness(P) #if two things are being returned, format like this to assign the things
    print('THIS IS STEP', step)
    print(w)
    if f == LENGTH:
        break
    P2 = []
    for i in range(SIZE):
        parent1 = parent(P, TSIZE)
        parent2 = parent(P, TSIZE)
        P2.append(mutation(crossover(parent1, parent2)))
    P = P2
        



#print(mutation('HELLO WORLD'))