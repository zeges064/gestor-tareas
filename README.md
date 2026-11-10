# Sistema de Gestión de Tareas – Plásticos Sustentables

Aplicación web en **Python + Flask + SQLite** para crear, asignar y hacer seguimiento
de tareas de los empleados.

## Funcionalidades
- Registro e inicio de sesión (contraseñas cifradas con `werkzeug.security`).
- Crear, editar y eliminar tareas (solo el creador puede editar o eliminar).
- Asignar tareas a usuarios específicos.
- Filtrar y buscar por texto, estado y prioridad.
- Ver tareas pendientes y completadas (la persona asignada puede completarlas).
- Gestión de perfil: editar datos y cambiar contraseña.

## Estructura
```
app.py            # Aplicación Flask (rutas, base de datos, autorización)
validators.py     # Validaciones reutilizables
templates/        # Vistas HTML
tests/            # Pruebas unitarias y de integración
.github/workflows/tests.yml   # Pruebas automáticas con GitHub Actions
```

## Ejecución
```bash
python -m venv venv
source venv/bin/activate          # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                     # http://127.0.0.1:5000
```

## Pruebas
```bash
pytest -v                                              # todas las pruebas
pytest --cov=app --cov=validators --cov-report=term-missing   # con cobertura
```
Los identificadores `CP-01` a `CP-11` en los nombres de las pruebas corresponden
a los casos del plan de pruebas.

## Notas
- Cambiar `SECRET_KEY` (variable de entorno) antes de un uso real.
- No incluye protección CSRF ni límite de intentos de login; son mejoras pendientes.
