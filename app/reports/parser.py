import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_SUBJECT_PATTERN = re.compile(r'\|\s*ASIGNATURA:\s*\((\d{3})\)\s*([^\|]+)')
_PERIOD_PATTERN = re.compile(r'PERIODO\s*:\s*([\w\-]+)')
_OBJECTIVE_PATTERN = re.compile(r'\|\d{2}\s')
_CEDULA_PATTERN = re.compile(r'\b([VEJP]-\d+)\b')
_WHITESPACE_PATTERN = re.compile(r'\s+')


@dataclass
class ParsedGrade:
    cedula: str
    full_name: str
    carrera_codigo: str
    nota_final: str
    condicion: str
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
                continue

            if "OBJETIVO" in line and current_subject_code:
                found = len(_OBJECTIVE_PATTERN.findall(line))
                max_objectives = found if found > 0 else -1
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

            if "No Presento" in resto:
                carrera_codigo = resto.split()[0]
                nombre = resto.replace(carrera_codigo, "").replace("No Presento", "").strip()
                condicion = "NP"
                nota_final = "No Presentó"
                absent = True
            else:
                tokens = resto.split()
                if not tokens:
                    continue
                carrera_codigo = tokens[0]
                nota_cruda = tokens[-1]
                nota_final = f"{nota_cruda}/{max_objectives}"

                letras_tokens = [t for t in tokens[1:-1] if not t.isdigit()]
                condicion = letras_tokens[-1] if letras_tokens else "N/A"

                nombre_tokens = []
                for t in tokens[1:]:
                    if t == condicion or t.isdigit():
                        break
                    nombre_tokens.append(t)
                nombre = " ".join(nombre_tokens)
                absent = False

            results.append(ParsedGrade(
                cedula=cedula,
                full_name=nombre,
                carrera_codigo=carrera_codigo,
                nota_final=nota_final,
                condicion=condicion,
                subject_code=current_subject_code,
                subject_name=current_subject_name,
                period_code=current_period_code,
                absent=absent,
            ))

    return results
