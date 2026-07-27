import csv
import asyncio
import json
import os
import random
from typing import Dict, List, Optional, Tuple


def read_csv_rows(file_path: str, skip_header: bool = False) -> List[List[str]]:
    with open(file_path, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
    if skip_header and rows:
        return rows[1:]
    return rows


def parse_scitimes(file_path: str) -> List[Dict[str, object]]:
    rows = read_csv_rows(file_path, skip_header=True)
    events = []
    for row in rows:
        if not row or not row[0].strip():
            continue
        name = row[0].strip()
        max_students = int(row[1]) if len(row) > 1 and row[1].strip().isdigit() else 999
        time_label = row[2].strip() if len(row) > 2 else ''
        is_build = time_label.lower() == 'n/a' or time_label == ''
        events.append({
            'name': name,
            'capacity': max_students,
            'time': None if is_build else time_label,
            'is_build': is_build,
        })
    return events


def parse_team_file(file_path: str, team_name: Optional[str] = None) -> List[Dict[str, object]]:
    if team_name is None:
        team_name = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        students = []
        for row in reader:
            if not row:
                continue
            name = ''
            for key, value in row.items():
                if key is None:
                    continue
                if key.strip().lower() == 'name':
                    name = (value or '').strip()
                    break
            if not name:
                continue
            prefs = {}
            for key, value in row.items():
                if key is None:
                    continue
                header = key.strip()
                if header.lower() in {'name', 'grade'}:
                    continue
                if not header:
                    continue
                try:
                    prefs[header] = int((value or '').strip())
                except Exception:
                    prefs[header] = 3
            students.append({
                'name': name,
                'team': team_name,
                'prefs': prefs,
            })
    return students


def combine_students(team_files: List[str]) -> List[Dict[str, object]]:
    all_students = []
    for path in team_files:
        team_name = os.path.splitext(os.path.basename(path))[0]
        all_students.extend(parse_team_file(path, team_name))
    return all_students


def event_weight(pref: int) -> int:
    return max(1, 4 - pref)


def weighted_sample_unique(items: List[str], weights: List[int], k: int) -> List[str]:
    if len(items) <= k:
        return list(items)
    chosen = []
    remaining = items[:]
    weight_map = {item: weight for item, weight in zip(items, weights)}
    while len(chosen) < k and remaining:
        total = sum(weight_map[item] for item in remaining)
        pick = random.uniform(0, total)
        current = 0.0
        for item in remaining:
            current += weight_map[item]
            if pick <= current:
                chosen.append(item)
                remaining.remove(item)
                break
    return chosen


def create_individual(students: List[Dict[str, object]], events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    timed_events = [event for event in events if not event['is_build']]
    build_events = [event for event in events if event['is_build']]
    schedule = []

    for student in students:
        prefs = student['prefs']
        timed_choices = [event['name'] for event in timed_events]
        timed_weights = [event_weight(prefs.get(name, 3)) for name in timed_choices]
        timed_assigned = weighted_sample_unique(timed_choices, timed_weights, min(3, len(timed_choices)))

        build_assigned = []
        build_candidates = [event['name'] for event in build_events if prefs.get(event['name'], 3) < 3]
        if build_candidates and len(timed_assigned) == 3:
            best_builds = [name for name in build_candidates if prefs.get(name, 3) == 1]
            if best_builds:
                build_assigned.append(random.choice(best_builds))
            elif random.random() < 0.4:
                build_assigned.append(random.choice(build_candidates))

        schedule.append({
            'student': student['name'],
            'team': student.get('team', 'Unknown Team'),
            'events': timed_assigned + build_assigned,
        })

    return schedule


def student_preference(student: Dict[str, object], event_name: str) -> int:
    return student['prefs'].get(event_name, 3)


def fitness(schedule: List[Dict[str, object]], students: List[Dict[str, object]], events: List[Dict[str, object]]) -> float:
    event_by_name = {event['name']: event for event in events}
    student_lookup = {student['name']: student for student in students}
    score = 0.0
    capacity_counts: Dict[str, int] = {event['name']: 0 for event in events}

    for assignment in schedule:
        student = student_lookup[assignment['student']]
        event_names = assignment['events']
        build_count = 0
        timed_count = 0
        times_seen = set()
        seen_events = set()

        if len(event_names) < 3:
            score -= 50 * (3 - len(event_names))
        if len(event_names) > 4:
            score -= 200 * (len(event_names) - 4)

        for event_name in event_names:
            if event_name in seen_events:
                score -= 100
                continue
            seen_events.add(event_name)
            event = event_by_name.get(event_name)
            if not event:
                score -= 30
                continue
            capacity_counts[event_name] += 1
            pref = student_preference(student, event_name)
            if event['is_build']:
                build_count += 1
                if pref == 1:
                    score += 12
                elif pref == 2:
                    score += 6
                else:
                    score -= 40
            else:
                timed_count += 1
                if pref == 1:
                    score += 10
                elif pref == 2:
                    score += 3
                else:
                    score -= 20
                time_label = event['time']
                if time_label in times_seen:
                    score -= 120
                times_seen.add(time_label)

        if timed_count > 3:
            score -= 80 * (timed_count - 3)
        if build_count > 3:
            score -= 150 * (build_count - 3)
        if timed_count == 4 and build_count == 0:
            score -= 40

    for event_name, count in capacity_counts.items():
        event = event_by_name[event_name]
        if count > event['capacity']:
            score -= 25 * (count - event['capacity'])

    return score


def parent(P: List[List[Dict[str, object]]], TSIZE: int, students: List[Dict[str, object]], events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    sample = random.sample(P, TSIZE)
    best = sample[0]
    best_fit = fitness(best, students, events)
    for individual in sample:
        fit = fitness(individual, students, events)
        if fit > best_fit:
            best = individual
            best_fit = fit
    return best


def crossover(parent1: List[Dict[str, object]], parent2: List[Dict[str, object]]) -> List[Dict[str, object]]:
    child = []
    for i in range(len(parent1)):
        child.append(parent1[i] if random.random() < 0.5 else parent2[i])
    return child


def mutation(child: List[Dict[str, object]], students: List[Dict[str, object]], events: List[Dict[str, object]], rate: float) -> List[Dict[str, object]]:
    build_events = [event['name'] for event in events if event['is_build']]
    timed_events = [event['name'] for event in events if not event['is_build']]
    event_by_name = {event['name']: event for event in events}
    mutated = []

    for assignment in child:
        student = next((s for s in students if s['name'] == assignment['student']), None)
        if not student:
            mutated.append(assignment)
            continue
        events_assigned = assignment['events'][:]
        if random.random() < rate:
            if events_assigned:
                replace_index = random.randrange(len(events_assigned))
                if any(event_by_name[e]['is_build'] for e in events_assigned):
                    if random.random() < 0.5:
                        candidate = random.choice(timed_events)
                    else:
                        candidate = random.choice(build_events)
                else:
                    candidate = random.choice(timed_events if random.random() < 0.8 else build_events)
                events_assigned[replace_index] = candidate
        if random.random() < rate:
            if len(events_assigned) < 4:
                build_candidates = [name for name in build_events if student_preference(student, name) < 3]
                if build_candidates and all(not event_by_name[e]['is_build'] for e in events_assigned):
                    events_assigned.append(random.choice(build_candidates))
        mutated.append({'student': assignment['student'], 'events': events_assigned})
    return mutated


def bestfitness(P: List[List[Dict[str, object]]], students: List[Dict[str, object]], events: List[Dict[str, object]]) -> Tuple[float, List[Dict[str, object]]]:
    best = P[0]
    best_fit = fitness(best, students, events)
    for individual in P:
        fit = fitness(individual, students, events)
        if fit > best_fit:
            best = individual
            best_fit = fit
    return best_fit, best


def build_schedule(
    events_file: str = 'SciTimes.csv',
    team_files: Optional[List[str]] = None,
    population_size: int = 120,
    max_no_improvement: int = 120,
    max_generations: int = 5000,
) -> Tuple[List[Dict[str, object]], float, List[Dict[str, object]], List[Dict[str, object]]]:
    if team_files is None:
        team_files = ['A Team.csv', 'B Team.csv']
    events = parse_scitimes(events_file)
    students = combine_students(team_files)
    population = [create_individual(students, events) for _ in range(population_size)]
    best_schedule = population[0]
    best_score = fitness(best_schedule, students, events)

    no_improve = 0
    generation = 0

    while no_improve < max_no_improvement and generation < max_generations:
        generation += 1
        scores = [fitness(individual, students, events) for individual in population]
        current_best = population[max(range(len(scores)), key=lambda i: scores[i])]
        current_best_score = max(scores)
        if current_best_score > best_score:
            best_score = current_best_score
            best_schedule = current_best
            no_improve = 0
        else:
            no_improve += 1

        next_population = []
        while len(next_population) < len(population):
            parent1 = parent(population, 5, students, events)
            parent2 = parent(population, 5, students, events)
            child = crossover(parent1, parent2)
            next_population.append(mutation(child, students, events, 0.18))
        population = next_population

    return best_schedule, best_score, students, events


async def build_schedule_async(
    events_file: str = 'SciTimes.csv',
    team_files: Optional[List[str]] = None,
    population_size: int = 120,
    max_no_improvement: int = 80,
    max_generations: int = 2000,
    yield_interval: int = 2,
) -> Tuple[List[Dict[str, object]], float, List[Dict[str, object]], List[Dict[str, object]]]:
    if team_files is None:
        team_files = ['A Team.csv', 'B Team.csv']
    events = parse_scitimes(events_file)
    students = combine_students(team_files)
    population = [create_individual(students, events) for _ in range(population_size)]
    best_schedule = population[0]
    best_score = fitness(best_schedule, students, events)

    no_improve = 0
    generation = 0

    while no_improve < max_no_improvement and generation < max_generations:
        generation += 1
        scores = [fitness(individual, students, events) for individual in population]
        current_best = population[max(range(len(scores)), key=lambda i: scores[i])]
        current_best_score = max(scores)
        if current_best_score > best_score:
            best_score = current_best_score
            best_schedule = current_best
            no_improve = 0
        else:
            no_improve += 1

        print(f'SOLVER_PROGRESS {generation}/{max_generations} best={best_score} stagnation={no_improve}/{max_no_improvement}')

        next_population = []
        child_counter = 0
        while len(next_population) < len(population):
            parent1 = parent(population, 5, students, events)
            parent2 = parent(population, 5, students, events)
            child = crossover(parent1, parent2)
            next_population.append(mutation(child, students, events, 0.18))
            child_counter += 1
            if child_counter % 24 == 0:
                await asyncio.sleep(0)
        population = next_population

        if generation % max(1, yield_interval) == 0:
            await asyncio.sleep(0)

    return best_schedule, best_score, students, events


def format_schedule(schedule: List[Dict[str, object]], students: List[Dict[str, object]], events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    event_map = {event['name']: event for event in events}
    student_teams = {student['name']: student.get('team', 'Unknown Team') for student in students}
    rows = []
    for assignment in schedule:
        row = {
            'team': assignment.get('team', student_teams.get(assignment['student'], 'Unknown Team')),
            'student': assignment['student'],
            'events': [],
        }
        for event_name in assignment['events']:
            event = event_map.get(event_name)
            if event:
                row['events'].append({
                    'name': event_name,
                    'time': event['time'] or 'build',
                })
            else:
                row['events'].append({'name': event_name, 'time': 'unknown'})
        rows.append(row)
    return rows


def format_schedule_by_event(schedule: List[Dict[str, object]], students: List[Dict[str, object]], events: List[Dict[str, object]]) -> List[Dict[str, object]]:
    preferred_team_order = ['A Team', 'B Team']
    student_teams = {student['name']: student.get('team', 'Unknown Team') for student in students}
    event_assignments: Dict[str, Dict[str, List[str]]] = {}

    for assignment in schedule:
        student_name = assignment.get('student', 'Unknown Student')
        team_name = assignment.get('team', student_teams.get(student_name, 'Unknown Team'))
        for event_name in assignment.get('events', []):
            if event_name not in event_assignments:
                event_assignments[event_name] = {}
            if team_name not in event_assignments[event_name]:
                event_assignments[event_name][team_name] = []
            event_assignments[event_name][team_name].append(student_name)

    rows = []
    seen_events = set()

    for event in events:
        event_name = event['name']
        seen_events.add(event_name)
        team_map = event_assignments.get(event_name, {})
        ordered_teams = [
            *[team for team in preferred_team_order if team in team_map],
            *[team for team in team_map.keys() if team not in preferred_team_order],
        ]

        if not ordered_teams:
            rows.append({'event': event_name, 'time': event['time'] or 'build', 'team': '—', 'students': []})
            continue

        for index, team_name in enumerate(ordered_teams):
            rows.append({
                'event': event_name if index == 0 else '',
                'time': (event['time'] or 'build') if index == 0 else '',
                'team': team_name,
                'students': team_map.get(team_name, []),
            })

    for event_name, team_map in event_assignments.items():
        if event_name in seen_events:
            continue
        ordered_teams = [
            *[team for team in preferred_team_order if team in team_map],
            *[team for team in team_map.keys() if team not in preferred_team_order],
        ]
        if not ordered_teams:
            rows.append({'event': event_name, 'time': 'unknown', 'team': '—', 'students': []})
            continue
        for index, team_name in enumerate(ordered_teams):
            rows.append({
                'event': event_name if index == 0 else '',
                'time': 'unknown' if index == 0 else '',
                'team': team_name,
                'students': team_map.get(team_name, []),
            })

    return rows


if __name__ == '__main__':
    schedule, score, students, events = asyncio.run(build_schedule_async())
    rows = format_schedule_by_event(schedule, students, events)
    print(f'Score: {score:.2f}')
    for entry in rows:
        student_text = ', '.join(entry['students']) if entry['students'] else 'No students assigned'
        print(entry['event'] or '...', '|', entry['time'] or '...', '|', entry['team'], '->', student_text)
