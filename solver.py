import csv
import io
import json
import random
from typing import Dict, List, Tuple


def parse_csv_text(text: str) -> List[List[str]]:
    if not text:
        return []
    reader = csv.reader(io.StringIO(text))
    return [row for row in reader if any(entry != "" for entry in row)]


def _find_column(headers: List[str], candidates: List[str]) -> int:
    lower_headers = [header.strip().lower() for header in headers]
    for candidate in candidates:
        if candidate.lower() in lower_headers:
            return lower_headers.index(candidate.lower())
    return -1


def _parse_int(value: str) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0


def _parse_time(value: str) -> int:
    if not value:
        return 0
    text = str(value).strip()
    if ":" in text:
        hour_text, minute_text = text.split(":", 1)
        try:
            return int(hour_text) * 60 + int(minute_text)
        except Exception:
            return 0
    try:
        return int(text)
    except Exception:
        return 0


def _parse_boolean(value: str) -> bool:
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "x"}


def parse_class_files(files: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    students_text = files.get("students", {}).get("text", "")
    teachers_text = files.get("teachers", {}).get("text", "")
    masterclasses_text = files.get("masterclasses", {}).get("text", "")
    groupclasses_text = files.get("groupclasses", {}).get("text", "")
    times_text = files.get("times", {}).get("text", "")

    students_rows = parse_csv_text(students_text)
    teachers_rows = parse_csv_text(teachers_text)
    masterclasses_rows = parse_csv_text(masterclasses_text)
    groupclasses_rows = parse_csv_text(groupclasses_text)
    times_rows = parse_csv_text(times_text)

    if len(students_rows) < 2 or len(teachers_rows) < 2 or len(masterclasses_rows) < 2 or len(groupclasses_rows) < 2 or len(times_rows) < 2:
        raise ValueError("Please upload all five CSV files with the expected headers.")

    students_header = students_rows[0]
    teachers_header = teachers_rows[0]
    masterclasses_header = masterclasses_rows[0]
    groupclasses_header = groupclasses_rows[0]
    times_header = times_rows[0]

    student_id_idx = _find_column(students_header, ["id", "student id", "studentid"])
    student_level_idx = _find_column(students_header, ["level", "book", "grade", "skill"])
    teacher_id_idx = _find_column(teachers_header, ["id", "teacher id", "teacherid"])
    teacher_level_idx = _find_column(teachers_header, ["level", "book", "grade", "skill"])
    class_id_idx = _find_column(masterclasses_header, ["id", "class id", "classid", "group id", "groupid"])
    class_level_idx = _find_column(masterclasses_header, ["level", "book", "grade", "skill"])
    group_id_idx = _find_column(groupclasses_header, ["id", "class id", "classid", "group id", "groupid"])
    group_level_idx = _find_column(groupclasses_header, ["level", "book", "grade", "skill"])
    time_id_idx = _find_column(times_header, ["id", "time id", "timeid"])
    time_label_idx = _find_column(times_header, ["time", "slot", "label"])

    students = []
    for row in students_rows[1:]:
        students.append({
            "id": row[student_id_idx] if student_id_idx >= 0 else row[0],
            "level": _parse_int(row[student_level_idx] if student_level_idx >= 0 else (row[2] if len(row) > 2 else 0)),
        })

    teachers = []
    for row in teachers_rows[1:]:
        teachers.append({
            "id": row[teacher_id_idx] if teacher_id_idx >= 0 else row[0],
            "level": _parse_int(row[teacher_level_idx] if teacher_level_idx >= 0 else (row[1] if len(row) > 1 else 0)),
        })

    classes = []
    for row in masterclasses_rows[1:]:
        class_id = row[class_id_idx] if class_id_idx >= 0 else row[0]
        class_level = _parse_int(row[class_level_idx] if class_level_idx >= 0 else (row[1] if len(row) > 1 else 0))
        student_ids = [entry.strip() for entry in row[(class_level_idx + 1) if class_level_idx >= 0 else 1:] if entry and entry.strip()]
        classes.append({"id": class_id, "level": class_level, "students": student_ids, "kind": "master"})

    for row in groupclasses_rows[1:]:
        class_id = row[group_id_idx] if group_id_idx >= 0 else row[0]
        class_level = _parse_int(row[group_level_idx] if group_level_idx >= 0 else (row[1] if len(row) > 1 else 0))
        student_ids = [entry.strip() for entry in row[(group_level_idx + 1) if group_level_idx >= 0 else 1:] if entry and entry.strip()]
        classes.append({"id": class_id, "level": class_level, "students": student_ids, "kind": "group"})

    times = []
    for row in times_rows[1:]:
        time_id = row[time_id_idx] if time_id_idx >= 0 else row[0]
        time_label = row[time_label_idx] if time_label_idx >= 0 else (row[1] if len(row) > 1 else time_id)
        times.append({"id": time_id, "label": time_label})

    return {"students": students, "teachers": teachers, "classes": classes, "times": times}


def _make_random_schedule(classes: List[Dict[str, object]], teachers: List[Dict[str, object]], times: List[Dict[str, object]], rng: random.Random) -> List[Dict[str, object]]:
    schedule = []
    for class_item in classes:
        eligible = [teacher for teacher in teachers if _parse_int(teacher["level"]) >= _parse_int(class_item["level"])]
        teacher = rng.choice(eligible) if eligible else rng.choice(teachers)
        time_item = rng.choice(times) if times else {"id": "1", "label": "1"}
        schedule.append({
            "class_id": class_item["id"],
            "teacher_id": teacher["id"],
            "time_id": time_item["id"],
            "students": class_item["students"],
        })
    return schedule


def _fitness(schedule: List[Dict[str, object]], classes: List[Dict[str, object]], teachers: List[Dict[str, object]]) -> float:
    teacher_levels = {teacher["id"]: _parse_int(teacher["level"]) for teacher in teachers}
    teacher_time_map = set()
    student_time_map = set()
    final_fitness = 0.0

    class_map = {class_item["id"]: class_item for class_item in classes}

    for assignment in schedule:
        class_item = class_map[assignment["class_id"]]
        teacher_level = teacher_levels.get(str(assignment["teacher_id"]), 0)
        class_level = _parse_int(class_item["level"])
        if teacher_level < class_level:
            return 0.0
        if class_level < teacher_level:
            final_fitness += teacher_level * (teacher_level - class_level) * (teacher_level - class_level)
        else:
            final_fitness += 0.000000001

        teacher_key = (str(assignment["teacher_id"]), str(assignment["time_id"]))
        if teacher_key in teacher_time_map:
            return 0.0
        teacher_time_map.add(teacher_key)

        for student_id in class_item["students"]:
            student_key = (str(student_id), str(assignment["time_id"]))
            if student_key in student_time_map:
                return 0.0
            student_time_map.add(student_key)

    return 1.0 / final_fitness if final_fitness > 0 else 0.0


def _crossover(parent_a: List[Dict[str, object]], parent_b: List[Dict[str, object]], rng: random.Random) -> List[Dict[str, object]]:
    child = []
    for index in range(len(parent_a)):
        child.append(parent_a[index] if rng.random() < 0.5 else parent_b[index])
    return child


def _mutate(schedule: List[Dict[str, object]], classes: List[Dict[str, object]], teachers: List[Dict[str, object]], times: List[Dict[str, object]], rng: random.Random) -> List[Dict[str, object]]:
    mutated = []
    for assignment in schedule:
        if rng.random() < 0.18:
            class_item = next((entry for entry in classes if entry["id"] == assignment["class_id"]), None)
            eligible = [teacher for teacher in teachers if _parse_int(teacher["level"]) >= _parse_int(class_item["level"])] if class_item else teachers
            teacher = rng.choice(eligible) if eligible else rng.choice(teachers)
            time_item = rng.choice(times) if times else {"id": "1", "label": "1"}
            mutated.append({
                "class_id": assignment["class_id"],
                "teacher_id": teacher["id"],
                "time_id": time_item["id"],
                "students": assignment["students"],
            })
        else:
            mutated.append(assignment)
    return mutated


def run_class_scheduling(data: Dict[str, object]) -> Dict[str, object]:
    classes = data.get("classes", [])
    teachers = data.get("teachers", [])
    times = data.get("times", [])

    if not classes or not teachers or not times:
        raise ValueError("Class scheduling needs classes, teachers, and times.")

    rng = random.Random(42)
    population_size = 120
    generations = 180
    population = [_make_random_schedule(classes, teachers, times, rng) for _ in range(population_size)]

    best_schedule = population[0]
    best_score = _fitness(best_schedule, classes, teachers)

    for _ in range(generations):
        scores = [_fitness(schedule, classes, teachers) for schedule in population]
        best_index = max(range(len(scores)), key=lambda i: scores[i])
        if scores[best_index] > best_score:
            best_score = scores[best_index]
            best_schedule = population[best_index]

        next_population = []
        while len(next_population) < population_size:
            parent_a = population[rng.randrange(population_size)]
            parent_b = population[rng.randrange(population_size)]
            child = _crossover(parent_a, parent_b, rng)
            next_population.append(_mutate(child, classes, teachers, times, rng))
        population = next_population

    return {"schedule": best_schedule, "score": best_score}


def format_class_schedule(result: Dict[str, object], data: Dict[str, object]) -> List[Dict[str, object]]:
    classes = data.get("classes", [])
    teachers = data.get("teachers", [])
    times = data.get("times", [])
    teacher_map = {teacher["id"]: teacher for teacher in teachers}
    time_map = {time["id"]: time for time in times}
    rows = []
    for assignment in result.get("schedule", []):
        class_item = next((entry for entry in classes if entry["id"] == assignment["class_id"]), None)
        if class_item is None:
            continue
        rows.append({
            "classId": assignment["class_id"],
            "classLevel": class_item["level"],
            "teacher": assignment["teacher_id"],
            "teacherLevel": teacher_map.get(str(assignment["teacher_id"]), {}).get("level", "n/a"),
            "time": time_map.get(str(assignment["time_id"]), {}).get("label", assignment["time_id"]),
            "students": class_item["students"],
        })
    return rows


def parse_ta_files(files: Dict[str, Dict[str, str]]) -> Dict[str, object]:
    labs_text = files.get("labs", {}).get("text", "")
    availability_text = files.get("availability", {}).get("text", "")

    labs_rows = parse_csv_text(labs_text)
    availability_rows = parse_csv_text(availability_text)

    if len(labs_rows) < 2 or len(availability_rows) < 2:
        raise ValueError("Please upload both the lab schedule CSV and the availability CSV.")

    lab_header = labs_rows[0]
    availability_header = availability_rows[0]
    lab_id_idx = _find_column(lab_header, ["id", "lab id", "labid", "name", "lab name"])
    start_idx = _find_column(lab_header, ["start", "start time", "time start", "begin"])
    end_idx = _find_column(lab_header, ["end", "end time", "time end"])

    labs = []
    for row in labs_rows[1:]:
        lab_id = row[lab_id_idx] if lab_id_idx >= 0 else row[0]
        start = _parse_time(row[start_idx] if start_idx >= 0 else (row[2] if len(row) > 2 else ""))
        end = _parse_time(row[end_idx] if end_idx >= 0 else (row[3] if len(row) > 3 else ""))
        labs.append({"id": lab_id, "start": start, "end": end})

    ta_names = [entry.strip() for entry in availability_header[1:] if entry and entry.strip()]
    availability = []
    for row_index, row in enumerate(availability_rows[1:]):
        lab_id = labs[row_index]["id"] if row_index < len(labs) else f"Lab {row_index + 1}"
        available_to = {}
        for ta_index, ta_name in enumerate(ta_names):
            raw_value = row[ta_index + 1] if ta_index + 1 < len(row) else ""
            available_to[ta_name] = _parse_boolean(raw_value)
        availability.append({"lab_id": lab_id, "available_to": available_to})

    return {"labs": labs, "availability": availability, "ta_names": ta_names}


def _labs_overlap(first: Dict[str, object], second: Dict[str, object]) -> bool:
    return first["start"] < second["end"] and second["start"] < first["end"]


def _make_random_ta_schedule(labs: List[Dict[str, object]], availability: List[Dict[str, object]], ta_names: List[str], rng: random.Random) -> List[Tuple[str, str]]:
    schedule = []
    for index, lab in enumerate(labs):
        available_options = [ta_name for ta_name in ta_names if availability[index]["available_to"].get(ta_name, False)]
        chosen = rng.choice(available_options) if available_options else (ta_names[0] if ta_names else "TA")
        schedule.append((lab["id"], chosen))
    return schedule


def _fitness_ta(schedule: List[Tuple[str, str]], labs: List[Dict[str, object]], availability: List[Dict[str, object]], ta_names: List[str]) -> float:
    counts = {ta_name: 0 for ta_name in ta_names}
    penalty = 0
    for index, (lab_id, ta_name) in enumerate(schedule):
        if ta_name not in availability[index]["available_to"] or not availability[index]["available_to"].get(ta_name, False):
            return 0.0
        counts[ta_name] += 1
        for compare_index in range(index):
            other_lab_id, other_ta_name = schedule[compare_index]
            if other_ta_name == ta_name and _labs_overlap(labs[index], labs[compare_index]):
                penalty += 5000

    ideal = len(labs) / max(1, len(ta_names))
    for ta_name in ta_names:
        penalty += abs(counts[ta_name] - ideal) * 40

    return -penalty


def run_ta_scheduling(data: Dict[str, object]) -> Dict[str, object]:
    labs = data.get("labs", [])
    availability = data.get("availability", [])
    ta_names = data.get("ta_names", [])

    if not labs or not availability or not ta_names:
        raise ValueError("TA scheduling needs labs, availability, and TA names.")

    rng = random.Random(42)
    population_size = 120
    generations = 180
    population = [_make_random_ta_schedule(labs, availability, ta_names, rng) for _ in range(population_size)]

    best_schedule = population[0]
    best_score = _fitness_ta(best_schedule, labs, availability, ta_names)

    for _ in range(generations):
        scores = [_fitness_ta(schedule, labs, availability, ta_names) for schedule in population]
        best_index = max(range(len(scores)), key=lambda i: scores[i])
        if scores[best_index] > best_score:
            best_score = scores[best_index]
            best_schedule = population[best_index]

        next_population = []
        while len(next_population) < population_size:
            parent_a = population[rng.randrange(population_size)]
            parent_b = population[rng.randrange(population_size)]
            child = []
            for index in range(len(parent_a)):
                child.append(parent_a[index] if rng.random() < 0.5 else parent_b[index])
            mutated = []
            for entry in child:
                if rng.random() < 0.18:
                    available_options = [ta_name for ta_name in ta_names if availability[len(mutated)]["available_to"].get(ta_name, False)]
                    chosen = rng.choice(available_options) if available_options else (ta_names[0] if ta_names else "TA")
                    mutated.append((entry[0], chosen))
                else:
                    mutated.append(entry)
            next_population.append(mutated)
        population = next_population

    return {"schedule": best_schedule, "score": best_score}


def format_ta_schedule(result: Dict[str, object], data: Dict[str, object]) -> List[Dict[str, object]]:
    labs = data.get("labs", [])
    rows = []
    for index, entry in enumerate(result.get("schedule", [])):
        lab = labs[index] if index < len(labs) else {"id": f"Lab {index + 1}", "start": "", "end": ""}
        rows.append({
            "lab": lab["id"],
            "ta": entry[1],
            "start": lab["start"],
            "end": lab["end"],
        })
    return rows


def solve_class_from_files(files_json: str) -> str:
    files = json.loads(files_json)
    data = parse_class_files(files)
    result = run_class_scheduling(data)
    rows = format_class_schedule(result, data)
    return json.dumps({"rows": rows, "score": result["score"]})


def solve_ta_from_files(files_json: str) -> str:
    files = json.loads(files_json)
    data = parse_ta_files(files)
    result = run_ta_scheduling(data)
    rows = format_ta_schedule(result, data)
    return json.dumps({"rows": rows, "score": result["score"]})
