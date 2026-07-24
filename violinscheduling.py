import random
import csv
import asyncio

from scheduling1 import POPULATION_SIZE

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
    
def converting_masterclasses(masterclasses):
    final = []
    for row in masterclasses:
        row[0] = row[0]
        row[1] = int(row[1])
        student_group = []
        student_group.append(int(row[2]))
        if row[3] != '':
            student_group.append(int(row[3]))
        if row[4] != '':
            student_group.append(int(row[4]))
        if row[5] != '':
            student_group.append(int(row[5]))
        r = (row[0], row[1], student_group)
        final.append(r)
    return final 
    
def create_individual(students, teachers, groupclasses, masterclasses, orchestra, times):
    schedule = []
    masterclass = converting_masterclasses(masterclasses)
    for row in masterclass:
        teacher_list = [teacher[0] for teacher in teachers if teacher[2] == row[1]]
        if len(teacher_list) == 0:
            teacher_list = [teacher[0]for teacher in teachers if teacher[2] > row[1]]
        class_teacher = random.choice(teacher_list)
        time_list = [time[0] for time in times]
        class_time = random.choice(time_list)
        class_schedule = (row[0], class_time, class_teacher, row[2])
        schedule.append(class_schedule)

    schedule_len = len(schedule)
    for row in groupclasses:
        student_list = [student[0] for student in students if student[2] == row[1]]
        for student in students:
            if student[2] == row[2]:
                student_list.append(student[0])
        # print(student_list)
        teacher_list = [teacher[0] for teacher in teachers 
                        if int(teacher[2]) >= int(row[1])]
        class_teacher = random.choice(teacher_list)
        time_list = [time[0] for time in times]
        class_time = random.choice(time_list)
        class_schedule = (row[0], class_time, class_teacher, student_list)
        schedule.append(class_schedule) 
    for row in orchestra:
        student_list = []
        # Add students whose book level appears in orchestra
        for student in students:
            if student[2] in row[1:]:
                student_list.append(student[0])
        class_time = random.choice([t[0] for t in times])
        class_schedule = (row[0], class_time, "ORCHESTRA", student_list)
        schedule.append(class_schedule)
    return schedule

def fitness(schedule, class_levels, teacher_levels):
    score = 100000
    teacher_time = {}
    student_time = {}
    hard_penalty = 0
    soft_penalty = 0
    # Check each class
    for c in schedule:
        classname = c[0]
        time = c[1]
        teacher = c[2]
        students = c[3]
        level = class_levels[classname]
        # Teacher level checking
        if teacher != "ORCHESTRA":
            teacher_level = teacher_levels[teacher]

            if teacher_level < level:
                hard_penalty += 1000

            elif teacher_level > level:
                soft_penalty += (teacher_level-level)*10


        # Teacher conflicts (INCLUDING ORCHESTRA)
        if teacher not in teacher_time:
            teacher_time[teacher] = []

        if time in teacher_time[teacher]:
            hard_penalty += 1000

        teacher_time[teacher].append(time)
        # Masterclass size limits
        if classname in class_levels:
            max_size = m_limits[level]
            actual_size = len(students)
            if actual_size > max_size:
                hard_penalty += (actual_size-max_size)*1000
            else:
                # reward full masterclasses
                missing = max_size - actual_size
                soft_penalty += missing*20
        # Teacher conflicts
        if teacher not in teacher_time:
            teacher_time[teacher] = []
        if time in teacher_time[teacher]:
            hard_penalty += 1000
        teacher_time[teacher].append(time)
        # Student conflicts
        for student in students:
            if student not in student_time:
                student_time[student] = []
            if time in student_time[student]:
                hard_penalty += 1000
            student_time[student].append(time)
    # Workload balancing
    teacher_total = len(teachers)
    total_classes = {}
    for teacher in teacher_time:
        if teacher not in total_classes:
            total_classes[teacher] = 0
        total_classes[teacher] += len(teacher_time[teacher])
    mean = len(schedule) / teacher_total
    for teacher in teachers:
        tid = teacher[0]
        actual = total_classes.get(tid,0)
        soft_penalty += abs(mean-actual)
    # Final score
    final_score = (
        score
        - hard_penalty
        - soft_penalty
    )
    #print("hard", hard_penalty, "soft", soft_penalty)
    return final_score

def parent(P, TSIZE):
    v = random.sample(P, TSIZE)

    best = v[0]
    best_fit = fitness(best, class_levels, teacher_levels)

    for individual in v:
        fit = fitness(individual, class_levels, teacher_levels)

        if fit > best_fit:
            best = individual
            best_fit = fit

    return best

def mutation(child):
    for i in range(len(child)):
        if random.random() < MUTATION_RATE:
            classname, time, teacher, students = child[i]
            # 95% chance: change time
            if random.random() < 0.8:
                time = random.choice([t[0] for t in times])
            # 5% chance: improve teacher
            else:
                required_level = class_levels[classname]
                possible = [
                    t for t in teachers
                    if int(t[2]) >= required_level
                ]
                best_level = min(
                    int(t[2])
                    for t in possible
                )
                best_teachers = [
                    t[0]
                    for t in possible
                    if int(t[2]) == best_level
                ]
                teacher = random.choice(best_teachers)
            child[i] = (classname, time, teacher, students)

    return child

def crossover(parent1, parent2):
    child = []

    for i in range(len(parent1)):
        if random.random() < 0.5:
            child.append(parent1[i])
        else:
            child.append(parent2[i])

    return child

def bestfitness(P):

    best = P[0]
    best_fit = fitness(best, class_levels, teacher_levels)

    for individual in P:

        fit = fitness(individual, class_levels, teacher_levels)

        if fit > best_fit:
            best = individual
            best_fit = fit

    return best_fit,best

file_path = 'Students.csv'
file_path2 = 'Teachers.csv'
file_path3 = 'Masterclasses.csv'
file_path4 = 'Times.csv'
file_path5 = 'Group Class.csv'
file_path6 = 'Orchestra.csv'
students = read_csv_to_2d_list(file_path)
for student in students:
    student[0] = int(student[0])
    student[2] = int(student[2])
teachers = read_csv_to_2d_list(file_path2)
for teacher in teachers:
    teacher[2] = int(teacher[2])
masterclasses = read_csv_to_2d_list(file_path3)
for item in masterclasses:
    item[0] = int(item[0])
    item[1] = int(item[1])
times = read_csv_to_2d_list(file_path4)
groupclasses = read_csv_to_2d_list(file_path5)
for item in groupclasses:
    item[0] = int(item[0])
    item[1] = int(item[1])
    if item[2] != '':
        item[2] = int(item[2])
orchestra = read_csv_to_2d_list(file_path6)
for item in orchestra:
    item[0] = int(item[0])
    for i in range(1, len(item)):
        if item[i] != '':
            item[i] = int(item[i])
student_total = len(students)
teachers_total = len(teachers)
m_limits = {1:4, 2:4, 3:4, 4:3, 5:3, 6:3, 7:2, 8:2} #limits for masterclasses by book level
POPULATION_SIZE = 500 #number of schedules in population
MUTATION_RATE = 0.25 #probability of mutation
GENERATIONS = 100 #max number of generations 
TSIZE = 5

class_levels = dict()
for item in masterclasses:
    class_levels[item[0]] = item[1]
for item in groupclasses:
    class_levels[item[0]] = item[1]
for item in orchestra:
    class_levels[item[0]] = item[1]

teacher_levels = dict()
for item in teachers:
    teacher_levels[item[0]] = item[2]
print(fitness(create_individual(students,teachers,groupclasses,masterclasses,orchestra,times), class_levels, teacher_levels))

best_score = 0
best_schedule = []

async def run_solver_async():
    global P, best_score, best_schedule
    P = [create_individual(students, teachers, groupclasses, masterclasses, orchestra, times)
         for _ in range(POPULATION_SIZE)]
    best_score, best_schedule = bestfitness(P)
    for generation in range(GENERATIONS):
        best_score, best_schedule = bestfitness(P)
        print(f'SOLVER_PROGRESS {generation + 1}/{GENERATIONS}')
        P2 = [best_schedule]
        while len(P2) < POPULATION_SIZE:
            parent1 = parent(P, TSIZE)
            parent2 = parent(P, TSIZE)
            child = mutation(crossover(parent1, parent2))
            P2.append(child)
        P = P2
        await asyncio.sleep(0)
    best_score, best_schedule = bestfitness(P)
    return best_score, best_schedule

if __name__ == '__main__':
    asyncio.run(run_solver_async())
    print("\nFINAL SCHEDULE")
    print("----------------")
    for item in best_schedule:
        print("Class:", item[0], "| Time:", item[1], "| Teacher:", item[2], "| Students:", item[3])