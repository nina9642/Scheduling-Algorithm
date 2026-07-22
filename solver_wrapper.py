import csv
import importlib.util
import io
import json
import os
import sys
import types


def _parse_csv_text(text):
    if text is None:
        return []
    reader = csv.reader(io.StringIO(text))
    return [row for row in reader if any(cell.strip() for cell in row)]


def _trim_python_script(source):
    lines = source.splitlines()
    trimmed = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("file_path =") or stripped.startswith("students = read_csv_to_2d_list(") or stripped.startswith("labs = read_csv_to_2d_list("):
            break
        trimmed.append(line)
    return "\n".join(trimmed)


def _create_scheduling1_stub():
    stub = types.ModuleType('scheduling1')
    stub.POPULATION_SIZE = 50
    sys.modules['scheduling1'] = stub
    return stub


def _load_module_from_text(name, path):
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), f'{name}.py')
    if not os.path.exists(path):
        raise FileNotFoundError(f'Module source not found: {path}')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    source = open(path, 'r', encoding='utf-8').read()
    trimmed_source = _trim_python_script(source)
    if name == 'violinscheduling':
        _create_scheduling1_stub()
    exec(trimmed_source, module.__dict__)
    return module


def _prepare_class_module(module, files):
    students = _parse_csv_text(files['students']['text'])
    teachers = _parse_csv_text(files['teachers']['text'])
    masterclasses = _parse_csv_text(files['masterclasses']['text'])
    groupclasses = _parse_csv_text(files['groupclasses']['text'])
    orchestra = _parse_csv_text(files['orchestra']['text'])
    times = _parse_csv_text(files['times']['text'])

    for row in students[1:]:
        if row:
            row[0] = int(row[0])
            row[2] = int(row[2])

    for row in teachers[1:]:
        if row:
            row[2] = int(row[2])

    for row in masterclasses[1:]:
        if row:
            row[1] = int(row[1])

    for row in groupclasses[1:]:
        if row:
            row[1] = int(row[1])
            if len(row) > 2 and row[2] != '':
                row[2] = int(row[2])

    for row in orchestra[1:]:
        if row:
            row[0] = int(row[0])
            for index in range(1, len(row)):
                if row[index] != '':
                    row[index] = int(row[index])

    module.students = students[1:]
    module.teachers = teachers[1:]
    module.masterclasses = masterclasses[1:]
    module.groupclasses = groupclasses[1:]
    module.orchestra = orchestra[1:]
    module.times = times[1:]
    module.student_total = len(students) - 1
    module.teachers_total = len(teachers)
    module.m_limits = {1: 4, 2: 4, 3: 4, 4: 3, 5: 3, 6: 3, 7: 2, 8: 2}
    module.POPULATION_SIZE = 500
    module.MUTATION_RATE = 0.25
    module.GENERATIONS = 100
    module.TSIZE = 5

    class_levels = {}
    for item in masterclasses:
        if item:
            class_levels[item[0]] = item[1]
    for item in groupclasses:
        if item:
            class_levels[item[0]] = item[1]
    for item in orchestra:
        if item:
            class_levels[item[0]] = item[1]

    teacher_levels = {item[0]: item[2] for item in teachers if item}
    module.class_levels = class_levels
    module.teacher_levels = teacher_levels

    return module


def _prepare_ta_module(module, files):
    labs = _parse_csv_text(files['labs']['text'])
    availability_all = _parse_csv_text(files['availability']['text'])
    if not availability_all:
        raise ValueError('Availability CSV must include a header and at least one lab row.')

    ta_names = availability_all[0][1:]
    availability = []
    for row in availability_all[1:]:
        if not row:
            continue
        lab_id = row[0]
        avail = [lab_id] + [1 if cell.strip().lower() in {'x', '1', 'true', 'yes'} else 0 for cell in row[1:]]
        availability.append(avail)

    for row in labs[1:]:
        if row:
            row[1] = int(row[1]) if row[1] != '' else 0
            row[2] = _parse_time(row[2]) if len(row) > 2 else 0
            row[3] = _parse_time(row[3]) if len(row) > 3 else 0

    module.labs = labs[1:]
    module.availability = availability
    module.ta_names = ta_names
    module.lab_total = len(labs) - 1
    module.ta_total = max(1, len(ta_names))
    module.mean = len(labs) / max(1, len(ta_names))
    module.POPULATION_SIZE = 1500
    module.MUTATION_RATE = 0.1
    module.GENERATIONS = 100
    module.TSIZE = 5
    return module


def _load_modules():
    violinsched = sys.modules.get('violinscheduling')
    if not violinsched:
        violinsched = _load_module_from_text('violinscheduling', os.path.join(os.path.dirname(__file__), 'violinscheduling.py'))
    tasched = sys.modules.get('TAscheduling')
    if not tasched:
        tasched = _load_module_from_text('TAscheduling', os.path.join(os.path.dirname(__file__), 'TAscheduling.py'))
    return violinsched, tasched


def _parse_time(value):
    if value is None:
        return 0
    text = str(value).strip()
    if ':' in text:
        parts = text.split(':', 1)
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return 0
    try:
        return int(text)
    except Exception:
        return 0


def solve_class_from_files(files_json):
    files = json.loads(files_json)
    violinsched, _ = _load_modules()
    _prepare_class_module(violinsched, files)

    P = [
        violinsched.create_individual(
            violinsched.students,
            violinsched.teachers,
            violinsched.groupclasses,
            violinsched.masterclasses,
            violinsched.orchestra,
            violinsched.times,
        )
        for _ in range(violinsched.POPULATION_SIZE)
    ]

    best_score, best_schedule = violinsched.bestfitness(P)
    for _ in range(violinsched.GENERATIONS):
        best_score, best_schedule = violinsched.bestfitness(P)
        P2 = [best_schedule]
        while len(P2) < violinsched.POPULATION_SIZE:
            parent1 = violinsched.parent(P, violinsched.TSIZE)
            parent2 = violinsched.parent(P, violinsched.TSIZE)
            child = violinsched.mutation(violinsched.crossover(parent1, parent2))
            P2.append(child)
        P = P2

    best_score, best_schedule = violinsched.bestfitness(P)

    teacher_names = {row[0]: row[1] for row in violinsched.teachers if row}
    time_names = {row[0]: row[1] for row in violinsched.times if row}

    rows = []
    for assignment in best_schedule:
        class_id, time_id, teacher_id, students = assignment
        rows.append({
            'classId': class_id,
            'teacher': teacher_names.get(teacher_id, teacher_id),
            'time': time_names.get(time_id, time_id),
            'students': len(students),
        })

    return json.dumps({'rows': rows, 'score': best_score})


def solve_ta_from_files(files_json):
    files = json.loads(files_json)
    _, tasched = _load_modules()
    _prepare_ta_module(tasched, files)

    P = [tasched.create_individual(tasched.availability) for _ in range(tasched.POPULATION_SIZE)]
    best_score, best_schedule = tasched.bestfitness(P)
    for _ in range(tasched.GENERATIONS):
        best_score, best_schedule = tasched.bestfitness(P)
        P2 = [best_schedule]
        while len(P2) < tasched.POPULATION_SIZE:
            parent1 = tasched.parent(P, tasched.TSIZE)
            parent2 = tasched.parent(P, tasched.TSIZE)
            child = tasched.mutation(tasched.crossover(parent1, parent2))
            P2.append(child)
        P = P2

    best_score, best_schedule = tasched.bestfitness(P)
    rows = []
    for index, entry in enumerate(best_schedule):
        lab_id = entry[0]
        ta_index = entry[1]
        ta_label = tasched.ta_names[ta_index - 1] if 1 <= ta_index <= len(tasched.ta_names) else str(ta_index)
        lab = tasched.labs[index] if index < len(tasched.labs) else ['', '', '', '']
        rows.append({
            'lab': lab_id,
            'ta': ta_label,
            'start': lab[2],
            'end': lab[3],
        })

    return json.dumps({'rows': rows, 'score': best_score})
