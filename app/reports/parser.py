import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_SUBJECT_PATTERN = re.compile(r'\|\s*ASIGNATURA:\s*\((\d{3})\)\s*([^\|]+)')
_PERIOD_PATTERN = re.compile(r'PERIODO\s*:\s*([\w\-]+)')
_OBJECTIVE_PATTERN = re.compile(r'\|\d{2}\s')
_CEDULA_PATTERN = re.compile(r'\b([VEJP]-\d+)\b')
_WHITESPACE_PATTERN = re.compile(r'\s+')

_KNOWN_COND = {'RG', 'RP', 'NP'}


@dataclass
class ParsedGrade:
    cedula: str
    full_name: str
    carrera_codigo: str
    condicion: str          # siempre el valor real: RG | RP (nunca "NP")
    objectives: list[bool]  # logros individuales [T1..T6]
    objectives_max: int     # máximo de objetivos posibles para la asignatura
    subject_code: str
    subject_name: str
    period_code: Optional[str]
    absent: bool


def parse_report(file_path: Path, encoding: str = 'latin-1') -> list[ParsedGrade]:
    results = []
    current_subject_code = None
    current_subject_name = None
    current_period_code = None
    max_objectives = 0

    with open(file_path, 'r', encoding=encoding) as f:
        for line in f:
            if "ASIGNATURA:" in line:
                match = _SUBJECT_PATTERN.search(line)
                if match:
                    current_subject_code = match.group(1).strip()
                    current_subject_name = match.group(2).strip()
                continue

            if "PERIODO" in line:
                match = _PERIOD_PATTERN.search(line)
                if match:
                    current_period_code = match.group(1).strip()
                if "OBJETIVO" in line and current_subject_code:
                    found = len(_OBJECTIVE_PATTERN.findall(line))
                    if found > 0:
                        max_objectives = found
                continue

            if "OBJETIVO" in line and current_subject_code:
                found = len(_OBJECTIVE_PATTERN.findall(line))
                if found > 0:
                    max_objectives = found
                continue

            cedula_match = _CEDULA_PATTERN.search(line)
            if not cedula_match or not current_subject_code:
                continue

            cedula = cedula_match.group(1)
            linea_limpia = _WHITESPACE_PATTERN.sub(' ', line.strip())
            partes = linea_limpia.split(cedula)

            if len(partes) <= 1:
                continue

            resto = partes[1].strip()
            tokens = resto.split()
            if not tokens:
                continue

            carrera_codigo = tokens[0]

            if "No" in tokens and "Presento" in tokens:
                # tokens: [carrera, ...nombre..., COND, "No", "Presento"]
                no_idx = tokens.index("No")
                pre_no = tokens[1:no_idx]
                if not pre_no:
                    continue
                condicion = pre_no[-1] if pre_no[-1] in _KNOWN_COND else "RG"
                nombre_tokens = pre_no[:-1] if pre_no[-1] in _KNOWN_COND else pre_no
                nombre = " ".join(nombre_tokens)
                objectives: list[bool] = []
                absent = True
            else:
                if max_objectives <= 0 or len(tokens) < max_objectives + 3:
                    continue
                # tokens: [carrera, ...nombre..., COND, obj_1..obj_n, total]
                obj_tokens = tokens[-(max_objectives + 1):-1]
                condicion = tokens[-(max_objectives + 2)]
                if condicion not in _KNOWN_COND:
                    condicion = "RG"
                nombre_tokens = tokens[1:-(max_objectives + 2)]
                nombre = " ".join(nombre_tokens)
                objectives = [t == "1" for t in obj_tokens]
                absent = False

            results.append(ParsedGrade(
                cedula=cedula,
                full_name=nombre,
                carrera_codigo=carrera_codigo,
                condicion=condicion,
                objectives=objectives,
                objectives_max=max_objectives,
                subject_code=current_subject_code,
                subject_name=current_subject_name,
                period_code=current_period_code,
                absent=absent,
            ))

    return results
