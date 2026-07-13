export function parseCSV(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];

    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          cell += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        cell += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
      continue;
    }

    if (char === ',') {
      row.push(cell.trim());
      cell = '';
      continue;
    }

    if (char === '\n') {
      row.push(cell.trim());
      if (row.some((entry) => entry !== '')) {
        rows.push(row);
      }
      row = [];
      cell = '';
      continue;
    }

    if (char === '\r') {
      continue;
    }

    cell += char;
  }

  if (cell !== '' || row.length) {
    row.push(cell.trim());
    if (row.some((entry) => entry !== '')) {
      rows.push(row);
    }
  }

  return rows;
}

function findColumn(headers, candidates) {
  for (const candidate of candidates) {
    const index = headers.findIndex((header) =>
      String(header).trim().toLowerCase() === candidate.toLowerCase()
    );
    if (index >= 0) {
      return index;
    }
  }
  return -1;
}

function normalizeLevel(value) {
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function parseTimeValue(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (typeof value === 'number') {
    return value;
  }
  const text = String(value).trim();
  if (/^\d+$/.test(text)) {
    return Number.parseInt(text, 10);
  }
  const parts = text.split(':');
  if (parts.length === 2) {
    const hours = Number.parseInt(parts[0], 10);
    const minutes = Number.parseInt(parts[1], 10);
    return hours * 60 + minutes;
  }
  return null;
}

function parseBooleanValue(value) {
  const text = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes', 'y', 'x'].includes(text)) {
    return true;
  }
  if (['0', 'false', 'no', 'n', ''].includes(text)) {
    return false;
  }
  return Boolean(value);
}

export function parseClassSchedulingData(files) {
  const studentsText = files.students?.text ? files.students.text : '';
  const teachersText = files.teachers?.text ? files.teachers.text : '';
  const masterclassesText = files.masterclasses?.text ? files.masterclasses.text : '';
  const groupclassesText = files.groupclasses?.text ? files.groupclasses.text : '';
  const timesText = files.times?.text ? files.times.text : '';

  const studentsRows = parseCSV(studentsText);
  const teachersRows = parseCSV(teachersText);
  const masterclassesRows = parseCSV(masterclassesText);
  const groupclassesRows = parseCSV(groupclassesText);
  const timesRows = parseCSV(timesText);

  if (studentsRows.length < 2 || teachersRows.length < 2 || masterclassesRows.length < 2 || groupclassesRows.length < 2 || timesRows.length < 2) {
    throw new Error('Please upload all five CSV files with the expected headers.');
  }

  const studentsHeader = studentsRows[0];
  const teachersHeader = teachersRows[0];
  const masterclassesHeader = masterclassesRows[0];
  const groupclassesHeader = groupclassesRows[0];
  const timesHeader = timesRows[0];

  const studentIdIndex = findColumn(studentsHeader, ['id', 'student id', 'studentid']);
  const studentLevelIndex = findColumn(studentsHeader, ['level', 'book', 'grade', 'skill']);
  const teacherIdIndex = findColumn(teachersHeader, ['id', 'teacher id', 'teacherid']);
  const teacherLevelIndex = findColumn(teachersHeader, ['level', 'book', 'grade', 'skill']);
  const classIdIndex = findColumn(masterclassesHeader, ['id', 'class id', 'classid', 'group id', 'groupid']);
  const classLevelIndex = findColumn(masterclassesHeader, ['level', 'book', 'grade', 'skill']);
  const groupClassIdIndex = findColumn(groupclassesHeader, ['id', 'class id', 'classid', 'group id', 'groupid']);
  const groupClassLevelIndex = findColumn(groupclassesHeader, ['level', 'book', 'grade', 'skill']);
  const timeIdIndex = findColumn(timesHeader, ['id', 'time id', 'timeid']);
  const timeLabelIndex = findColumn(timesHeader, ['time', 'slot', 'label']);

  const students = studentsRows.slice(1).map((row) => ({
    id: row[studentIdIndex >= 0 ? studentIdIndex : 0],
    level: normalizeLevel(row[studentLevelIndex >= 0 ? studentLevelIndex : 2]),
  }));

  const teachers = teachersRows.slice(1).map((row) => ({
    id: row[teacherIdIndex >= 0 ? teacherIdIndex : 0],
    level: normalizeLevel(row[teacherLevelIndex >= 0 ? teacherLevelIndex : 1]),
  }));

  const masterclasses = masterclassesRows.slice(1).map((row) => ({
    id: row[classIdIndex >= 0 ? classIdIndex : 0],
    level: normalizeLevel(row[classLevelIndex >= 0 ? classLevelIndex : 1]),
    students: row.slice((classLevelIndex >= 0 ? classLevelIndex : 1) + 1).filter(Boolean).map((value) => String(value).trim()),
  }));

  const groupclasses = groupclassesRows.slice(1).map((row) => ({
    id: row[groupClassIdIndex >= 0 ? groupClassIdIndex : 0],
    level: normalizeLevel(row[groupClassLevelIndex >= 0 ? groupClassLevelIndex : 1]),
    students: row.slice((groupClassLevelIndex >= 0 ? groupClassLevelIndex : 1) + 1).filter(Boolean).map((value) => String(value).trim()),
  }));

  const times = timesRows.slice(1).map((row) => ({
    id: row[timeIdIndex >= 0 ? timeIdIndex : 0],
    label: row[timeLabelIndex >= 0 ? timeLabelIndex : 1] || row[timeIdIndex >= 0 ? timeIdIndex : 0],
  }));

  return {
    students,
    teachers,
    classes: [...masterclasses, ...groupclasses],
    times,
  };
}

function createRandomSchedule(classes, teachers, times) {
  const eligibleTeachers = classes.map((classItem) =>
    teachers
      .filter((teacher) => teacher.level >= classItem.level)
      .map((teacher) => teacher.id)
  );

  return classes.map((classItem, classIndex) => {
    const teacherOptions = eligibleTeachers[classIndex];
    const teacherId = teacherOptions.length > 0 ? teacherOptions[Math.floor(Math.random() * teacherOptions.length)] : teachers[0]?.id;
    return {
      classId: classItem.id,
      teacherId,
      timeId: times[Math.floor(Math.random() * times.length)].id,
    };
  });
}

function cloneSchedule(schedule) {
  return schedule.map((entry) => ({ ...entry }));
}

function evaluateSchedule(schedule, classes, teachers) {
  const teacherTimeMap = new Map();
  const studentTimeMap = new Map();
  let score = 0;
  let conflicts = 0;

  for (let index = 0; index < schedule.length; index += 1) {
    const assignment = schedule[index];
    const classItem = classes[index];
    const teacher = teachers.find((teacherEntry) => teacherEntry.id === assignment.teacherId);
    if (!teacher || teacher.level < classItem.level) {
      return Number.NEGATIVE_INFINITY;
    }

    score += teacher.level - classItem.level + 1;

    const teacherKey = `${assignment.teacherId}:${assignment.timeId}`;
    if (teacherTimeMap.has(teacherKey)) {
      conflicts += 1000;
    } else {
      teacherTimeMap.set(teacherKey, true);
    }

    for (const studentId of classItem.students) {
      const studentKey = `${studentId}:${assignment.timeId}`;
      if (studentTimeMap.has(studentKey)) {
        conflicts += 1000;
      } else {
        studentTimeMap.set(studentKey, true);
      }
    }
  }

  return score - conflicts;
}

function crossover(parentA, parentB) {
  const child = [];
  for (let index = 0; index < parentA.length; index += 1) {
    child.push(Math.random() > 0.5 ? { ...parentA[index] } : { ...parentB[index] });
  }
  return child;
}

function mutateSchedule(schedule, classes, teachers, times) {
  const next = cloneSchedule(schedule);
  const mutationRate = 0.18;

  for (let index = 0; index < next.length; index += 1) {
    if (Math.random() < mutationRate) {
      const classItem = classes[index];
      const eligibleTeachers = teachers.filter((teacher) => teacher.level >= classItem.level);
      const teacher = eligibleTeachers[Math.floor(Math.random() * eligibleTeachers.length)] || teachers[0];
      next[index] = {
        ...next[index],
        teacherId: teacher.id,
        timeId: times[Math.floor(Math.random() * times.length)].id,
      };
    }
  }

  return next;
}

function selectParent(population, scores) {
  const tournamentSize = 4;
  let bestIndex = 0;
  let bestScore = Number.NEGATIVE_INFINITY;

  for (let i = 0; i < tournamentSize; i += 1) {
    const candidateIndex = Math.floor(Math.random() * population.length);
    if (scores[candidateIndex] > bestScore) {
      bestScore = scores[candidateIndex];
      bestIndex = candidateIndex;
    }
  }
  return population[bestIndex];
}

export function runClassScheduling(data) {
  const { classes, teachers, times } = data;
  const populationSize = 90;
  const generations = 140;
  const population = Array.from({ length: populationSize }, () => createRandomSchedule(classes, teachers, times));

  let bestSchedule = population[0];
  let bestScore = Number.NEGATIVE_INFINITY;

  for (let generation = 0; generation < generations; generation += 1) {
    const scores = population.map((schedule) => evaluateSchedule(schedule, classes, teachers));

    for (let index = 0; index < population.length; index += 1) {
      if (scores[index] > bestScore) {
        bestScore = scores[index];
        bestSchedule = cloneSchedule(population[index]);
      }
    }

    const nextPopulation = [];
    while (nextPopulation.length < populationSize) {
      const parentA = selectParent(population, scores);
      const parentB = selectParent(population, scores);
      const child = crossover(parentA, parentB);
      nextPopulation.push(mutateSchedule(child, classes, teachers, times));
    }
    population.splice(0, population.length, ...nextPopulation);
  }

  const finalScores = population.map((schedule) => evaluateSchedule(schedule, classes, teachers));
  const bestIndex = finalScores.indexOf(Math.max(...finalScores));
  const finalBest = population[bestIndex];
  const finalScore = evaluateSchedule(finalBest, classes, teachers);
  if (finalScore > bestScore) {
    bestScore = finalScore;
    bestSchedule = cloneSchedule(finalBest);
  }

  return {
    schedule: bestSchedule,
    score: bestScore,
  };
}

export function formatClassSchedule(result, data) {
  const { classes, teachers, times } = data;
  const teacherMap = Object.fromEntries(teachers.map((teacher) => [teacher.id, teacher]));
  const timeMap = Object.fromEntries(times.map((time) => [time.id, time]));
  return result.schedule.map((assignment, index) => ({
    classId: assignment.classId,
    classLevel: classes[index].level,
    teacher: teacherMap[assignment.teacherId]?.id || assignment.teacherId,
    teacherLevel: teacherMap[assignment.teacherId]?.level || 'n/a',
    time: timeMap[assignment.timeId]?.label || assignment.timeId,
    students: classes[index].students,
  }));
}

export function parseTaSchedulingData(files) {
  const labsText = files.labs?.text ? files.labs.text : '';
  const availabilityText = files.availability?.text ? files.availability.text : '';

  const labsRows = parseCSV(labsText);
  const availabilityRows = parseCSV(availabilityText);
  if (labsRows.length < 2 || availabilityRows.length < 2) {
    throw new Error('Please upload both the lab schedule CSV and the availability CSV.');
  }

  const availabilityHeader = availabilityRows[0];
  const labHeader = labsRows[0];
  const labIdIndex = findColumn(labHeader, ['id', 'lab id', 'labid', 'name']);
  const startIndex = findColumn(labHeader, ['start', 'start time', 'time start', 'begin']);
  const endIndex = findColumn(labHeader, ['end', 'end time', 'time end']);

  const taNames = availabilityHeader.slice(1).map((entry) => String(entry).trim()).filter(Boolean);

  const labs = labsRows.slice(1).map((row, index) => ({
    id: row[labIdIndex >= 0 ? labIdIndex : 0] || `Lab ${index + 1}`,
    start: parseTimeValue(row[startIndex >= 0 ? startIndex : 1]),
    end: parseTimeValue(row[endIndex >= 0 ? endIndex : 2]),
  }));

  const availability = availabilityRows.slice(1).map((row, index) => ({
    labId: labs[index]?.id || `Lab ${index + 1}`,
    availableTo: Object.fromEntries(
      taNames.map((taName, taIndex) => [taName, parseBooleanValue(row[taIndex + 1] ?? '')])
    ),
  }));

  return { labs, availability, taNames };
}

function overlaps(a, b) {
  if (a.start === null || a.end === null || b.start === null || b.end === null) {
    return false;
  }
  return a.start < b.end && b.start < a.end;
}

function createRandomTaSchedule(labs, availability, taNames) {
  return labs.map((lab, index) => {
    const labAvailability = availability[index] || { availableTo: {} };
    const eligible = taNames.filter((taName) => labAvailability.availableTo[taName] === true);
    const fallback = taNames[0] || 'TA 1';
    return eligible.length > 0 ? eligible[Math.floor(Math.random() * eligible.length)] : fallback;
  });
}

export function runTaScheduling(data) {
  const { labs, availability, taNames } = data;
  const populationSize = 90;
  const generations = 120;

  const taIds = taNames.length > 0 ? taNames : availability.map((entry) => entry.labId);
  const population = Array.from({ length: populationSize }, () => createRandomTaSchedule(labs, availability, taNames));
  let bestSchedule = population[0];
  let bestScore = Number.NEGATIVE_INFINITY;

  const evaluate = (schedule) => {
    let score = 0;
    let conflicts = 0;
    const counts = Object.fromEntries(taIds.map((id) => [id, 0]));

    for (let index = 0; index < schedule.length; index += 1) {
      const assignedTa = schedule[index];
      const lab = labs[index];
      const labAvailability = availability[index] || { availableTo: {} };
      if (labAvailability.availableTo[assignedTa] !== true) {
        return Number.NEGATIVE_INFINITY;
      }

      counts[assignedTa] += 1;
      for (let compare = 0; compare < index; compare += 1) {
        if (schedule[compare] === assignedTa) {
          if (overlaps(lab, labs[compare])) {
            conflicts += 1000;
          }
        }
      }
    }

    const ideal = labs.length / taIds.length;
    for (const taId of taIds) {
      score += 14 - Math.abs(counts[taId] - ideal);
    }
    return score - conflicts;
  };

  const mutate = (schedule) => {
    const next = [...schedule];
    const mutationRate = 0.18;
    for (let index = 0; index < next.length; index += 1) {
      if (Math.random() < mutationRate) {
        next[index] = taIds[Math.floor(Math.random() * taIds.length)];
      }
    }
    return next;
  };

  const crossover = (parentA, parentB) => {
    const child = [];
    for (let index = 0; index < parentA.length; index += 1) {
      child.push(Math.random() > 0.5 ? parentA[index] : parentB[index]);
    }
    return child;
  };

  const select = (candidatePopulation, scores) => {
    const tournamentSize = 4;
    let bestScore = Number.NEGATIVE_INFINITY;
    let bestIndex = 0;
    for (let i = 0; i < tournamentSize; i += 1) {
      const index = Math.floor(Math.random() * candidatePopulation.length);
      if (scores[index] > bestScore) {
        bestScore = scores[index];
        bestIndex = index;
      }
    }
    return candidatePopulation[bestIndex];
  };

  for (let generation = 0; generation < generations; generation += 1) {
    const scores = population.map((schedule) => evaluate(schedule));
    for (let index = 0; index < population.length; index += 1) {
      if (scores[index] > bestScore) {
        bestScore = scores[index];
        bestSchedule = [...population[index]];
      }
    }

    const nextPopulation = [];
    while (nextPopulation.length < populationSize) {
      const parentA = select(population, scores);
      const parentB = select(population, scores);
      const child = crossover(parentA, parentB);
      nextPopulation.push(mutate(child));
    }

    population.splice(0, population.length, ...nextPopulation);
  }

  return {
    schedule: bestSchedule,
    score: bestScore,
  };
}

export function formatTaSchedule(result, data) {
  const { labs } = data;
  return result.schedule.map((taId, index) => ({
    lab: labs[index].id,
    ta: taId,
    start: labs[index].start,
    end: labs[index].end,
  }));
}
