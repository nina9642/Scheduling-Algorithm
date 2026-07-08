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
    
def create_individual(students, teachers, groupclasses):
    schedule = []
    masterclass = converting_masterclasses(masterclasses)
    for row in masterclass:
        teacher_list = [teacher[0] for teacher in teachers if teacher[2] >= row[1]]
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
    return schedule

def fitness(schedule, class_levels, teacher_levels):
    final_fitness = 0
    for c in schedule:
        cl = class_levels[c[0]]
        tl = teacher_levels[c[2]]
        if cl > tl:
            return 0, 'the error occurred when cl > tl'
        if cl < tl:
            final_fitness += tl*(tl - cl)*(tl - cl)
        if cl == tl:
            final_fitness += 0.000000001
        #print(final_fitness)
    teacher_time = dict()
    student_time = dict()
    for c in schedule:
        #print('step', c)
        tid = int(c[2]) #teacher id
        t = c[1] #class time
        if tid not in teacher_time:
            teacher_time[tid] = set()
        if t in teacher_time[tid]:
            return 0, 'the error occurred when t in tid'
        else:
            teacher_time[tid].add(t)
        #print(teacher_time)
        sid = c[3] #student list
        for s in sid:
            if s not in student_time:
                student_time[s] = set()
            if t in student_time[s]:
                return 0, 'the error occurred when t in sid'
            else:
                student_time[s].add(t)
            #print(student_time)
    
    return 1/final_fitness


file_path = 'Students.csv'
file_path2 = 'Teachers.csv'
file_path3 = 'Masterclasses.csv'
file_path4 = 'Times.csv'
file_path5 = 'Group Class.csv'
students = read_csv_to_2d_list(file_path)
for student in students:
    student[2] = int(student[2])
teachers = read_csv_to_2d_list(file_path2)
for teacher in teachers:
    teacher[2] = int(teacher[2])
masterclasses = read_csv_to_2d_list(file_path3)
for item in masterclasses:
    item[1] = int(item[1])
times = read_csv_to_2d_list(file_path4)
groupclasses = read_csv_to_2d_list(file_path5)
for item in groupclasses:
    item[1] = int(item[1])
    if item[2] != '':
        item[2] = int(item[2])
student_total = len(students)
teachers_total = len(teachers)
limits = {1:4, 2:4, 3:4, 4:3, 5:3, 6:3, 7:2, 8:2}

class_levels = dict()
for item in masterclasses:
    class_levels[item[0]] = item[1]
for item in groupclasses:
    class_levels[item[0]] = item[1]

teacher_levels = dict()
for item in teachers:
    teacher_levels[item[0]] = item[2]
print(fitness(create_individual(students,teachers,groupclasses), class_levels, teacher_levels))
#print(create_individual(students,teachers,groupclasses), class_levels, teacher_levels)

