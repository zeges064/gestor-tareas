"""Pruebas unitarias de las validaciones (CP-02, CP-06)."""
import unittest

from validators import (validar_email, validar_fecha, validar_password,
                        validar_tarea)


class TestEmail(unittest.TestCase):
    def test_email_valido(self):
        self.assertTrue(validar_email("ana@empresa.com"))

    def test_email_invalido(self):
        for malo in ("", "ana", "ana@", "ana@empresa", "a na@x.com", None):
            self.assertFalse(validar_email(malo), malo)


class TestPassword(unittest.TestCase):
    def test_password_valida(self):
        self.assertTrue(validar_password("Clave1234"))

    def test_password_corta(self):
        self.assertFalse(validar_password("abc12"))

    def test_password_sin_numero(self):
        self.assertFalse(validar_password("sololetras"))

    def test_password_sin_letra(self):
        self.assertFalse(validar_password("12345678"))

    def test_password_vacia(self):
        self.assertFalse(validar_password(""))


class TestFecha(unittest.TestCase):
    def test_fecha_valida_y_vacia(self):
        self.assertTrue(validar_fecha("2026-12-31"))
        self.assertTrue(validar_fecha(""))
        self.assertTrue(validar_fecha(None))

    def test_fecha_invalida(self):
        self.assertFalse(validar_fecha("31/12/2026"))
        self.assertFalse(validar_fecha("2026-13-40"))


class TestTarea(unittest.TestCase):
    def test_tarea_valida(self):
        self.assertEqual(validar_tarea("Revisar molde", "alta", "2026-12-01"), [])

    def test_titulo_vacio(self):
        self.assertTrue(validar_tarea("   ", "media", None))

    def test_titulo_muy_largo(self):
        self.assertTrue(validar_tarea("x" * 101, "media", None))

    def test_prioridad_invalida(self):
        self.assertTrue(validar_tarea("Tarea", "urgente", None))

    def test_fecha_invalida(self):
        self.assertTrue(validar_tarea("Tarea", "baja", "ayer"))


if __name__ == "__main__":
    unittest.main()
