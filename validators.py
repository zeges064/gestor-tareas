"""Funciones de validación reutilizables (se prueban de forma unitaria)."""
import re
from datetime import datetime

PRIORIDADES = ("baja", "media", "alta")
ESTADOS = ("pendiente", "completada")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_email(email):
    return bool(email) and bool(EMAIL_RE.match(email))


def validar_password(password):
    """Mínimo 8 caracteres, al menos una letra y un número."""
    if not password or len(password) < 8:
        return False
    return any(c.isalpha() for c in password) and any(c.isdigit() for c in password)


def validar_fecha(fecha):
    """Fecha opcional en formato AAAA-MM-DD."""
    if not fecha:
        return True
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validar_tarea(titulo, prioridad, fecha_limite):
    """Devuelve una lista de errores (vacía si todo está bien)."""
    errores = []
    if not titulo or not titulo.strip():
        errores.append("El título es obligatorio.")
    elif len(titulo.strip()) > 100:
        errores.append("El título no puede superar 100 caracteres.")
    if prioridad not in PRIORIDADES:
        errores.append("La prioridad no es válida.")
    if not validar_fecha(fecha_limite):
        errores.append("La fecha límite debe tener el formato AAAA-MM-DD.")
    return errores
