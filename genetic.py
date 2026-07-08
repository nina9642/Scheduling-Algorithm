import random

def f(x,y,z):
    return 5*x**3 + 3*y**2 + 2*z**5 - 25

def fitness(x,y,z):
    v = f(x,y,z)
    if v == 0:
        return 1000000
    else:
        return abs(1/v)

max = 1000
size = 1000
max_steps = 10000
max_fitness = 1000000

L = []
P = []

for n in range(0,size):
    x = random.uniform(0,max) #uniform chooses a number randomly and equally from the range
    y = random.uniform(0,max)
    z = random.uniform(0,max)
    L.append((fitness(x,y,z),(x,y,z)))
    P.append((x,y,z))

for j in range(0,max_steps):

    L.sort(reverse=True) #sort should be before the if/else since that's optimal time use
    if L[0][0] >= 100000:
        break
    else:
        L = L[:100]
        L2 = [] #new lists must be inside loop or else they're just empty over and over again 
        P2 = [] 
        for i in range(0,size):
            x = random.choice(L)[1][0] #use L to get x,y,z because that's where they've been sorted
            x = x * random.uniform(0.99,1.01)
            y = random.choice(L)[1][1]
            y = y * random.uniform(0.99,1.01)
            z = random.choice(L)[1][2]
            z = z * random.uniform(0.99,1.01)
            L2.append((fitness(x,y,z),(x,y,z))) #this will have 1000 items after the for loop
            P2.append((x,y,z)) #population must always be 1000
        L = L2
        P = P2 #reiterate what you want your list and population to be since it will be referenced as L/P

print(L[0][0])

#print(P)
# print(f(1,2,3))
# print(fitness(1,2,3))
#print(L)