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

# Example usage
file_path = 'Lab Schedule.csv'
file_path2 = 'Availability.csv'
labs = read_csv_to_2d_list(file_path)
availability = read_csv_to_2d_list(file_path2)

# Print the 2D list
for row in labs:
    row[1] = int(row[1])
    row[2] = str_to_int(row[2])
    row[3] = str_to_int(row[3])
    print(row)

for row in availability:
    for i in range(1,len(row)):
        if row[i] == '':
            row[i] = 0
        else:
            row[i] = 1
    #print(row)

#print(str_to_int(labs[3][2]))

print(overlap(1,3,2,4))