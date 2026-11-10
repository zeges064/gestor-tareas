"""Utilidades comunes para las pruebas de integración."""
import os
import tempfile
import unittest

from app import create_app


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.fd, self.ruta_db = tempfile.mkstemp(suffix=".db")
        self.app = create_app({"TESTING": True, "DATABASE": self.ruta_db,
                               "SECRET_KEY": "test"})
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.fd)
        os.unlink(self.ruta_db)

    # --- ayudas ---
    def registrar(self, nombre="Ana", email="ana@empresa.com",
                  password="Clave1234", client=None):
        return (client or self.client).post("/register", data={
            "nombre": nombre, "email": email, "password": password},
            follow_redirects=True)

    def login(self, email="ana@empresa.com", password="Clave1234", client=None):
        return (client or self.client).post("/login", data={
            "email": email, "password": password}, follow_redirects=True)

    def crear_usuario_y_entrar(self, **kw):
        self.registrar(**{k: v for k, v in kw.items() if k != "client"})
        return self.login(kw.get("email", "ana@empresa.com"),
                          kw.get("password", "Clave1234"))

    def nueva_tarea(self, titulo="Revisar molde", prioridad="media",
                    asignado_id=1, client=None, **extra):
        data = {"titulo": titulo, "descripcion": "", "prioridad": prioridad,
                "fecha_limite": "", "asignado_id": asignado_id}
        data.update(extra)
        return (client or self.client).post("/tareas/nueva", data=data,
                                            follow_redirects=True)

    def segundo_cliente(self):
        """Cliente independiente con otro usuario (Luis, id=2) autenticado."""
        otro = self.app.test_client()
        self.registrar("Luis", "luis@empresa.com", client=otro)
        self.login("luis@empresa.com", client=otro)
        return otro
