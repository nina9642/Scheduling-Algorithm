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

P = [(random.uniform(0,max), random.uniform(0,max), random.uniform(0,max)) for n in range(0,size)]
L = [(fitness(s[0],s[1],s[2]),s) for s in P]

for j in range(0,max_steps):
    L.sort(reverse=True) 
    
    if L[0][0] >= 100000:
        break
    else:
        L = L[:100]
        P2 = [(random.choice(L)[1][0]*random.uniform(0.99,1.01), 
               random.choice(L)[1][1]*random.uniform(0.99,1.01), 
               random.choice(L)[1][2]*random.uniform(0.99,1.01)) for i in range(0,size)]
        L2 = [(fitness(n[0], n[1], n[2]), (n)) for n in P2]
        L = L2
        P = P2 

print(L[0][0])
