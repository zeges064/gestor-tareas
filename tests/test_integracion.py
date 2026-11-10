"""Pruebas de integración: rutas Flask + base de datos (CP-01 a CP-11)."""
from tests.base import BaseTestCase


class TestRegistroYLogin(BaseTestCase):
    def test_cp01_registro_valido(self):
        r = self.registrar()
        self.assertIn("Cuenta creada", r.get_data(as_text=True))

    def test_cp02_registro_correo_repetido(self):
        self.registrar()
        r = self.registrar()
        self.assertIn("ya está registrado", r.get_data(as_text=True))

    def test_cp02_registro_password_debil(self):
        r = self.registrar(password="123")
        self.assertIn("mínimo 8 caracteres", r.get_data(as_text=True))

    def test_cp03_login_valido(self):
        self.registrar()
        r = self.login()
        self.assertIn("Mis tareas", r.get_data(as_text=True))

    def test_cp04_login_password_incorrecta(self):
        self.registrar()
        r = self.login(password="Equivocada1")
        self.assertIn("incorrectos", r.get_data(as_text=True))

    def test_ruta_protegida_redirige_a_login(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers["Location"])

    def test_logout_cierra_sesion(self):
        self.crear_usuario_y_entrar()
        self.client.get("/logout")
        self.assertEqual(self.client.get("/").status_code, 302)


class TestTareas(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.crear_usuario_y_entrar()  # Ana, id=1

    def test_cp06_crear_tarea_titulo_vacio(self):
        r = self.nueva_tarea(titulo="")
        self.assertIn("título es obligatorio", r.get_data(as_text=True))

    def test_cp07_crear_editar_eliminar(self):
        r = self.nueva_tarea("Mantener extrusora")
        self.assertIn("Mantener extrusora", r.get_data(as_text=True))
        r = self.client.post("/tareas/1/editar", data={
            "titulo": "Mantener extrusora 2", "descripcion": "",
            "prioridad": "alta", "fecha_limite": "", "asignado_id": 1},
            follow_redirects=True)
        self.assertIn("Mantener extrusora 2", r.get_data(as_text=True))
        r = self.client.post("/tareas/1/eliminar", follow_redirects=True)
        self.assertNotIn("Mantener extrusora 2", r.get_data(as_text=True))

    def test_cp08_asignar_tarea_a_otro_usuario(self):
        otro = self.segundo_cliente()  # Luis, id=2
        self.nueva_tarea("Entregar lote", asignado_id=2)
        r = otro.get("/")
        self.assertIn("Entregar lote", r.get_data(as_text=True))

    def test_cp09_filtrar_y_buscar(self):
        self.nueva_tarea("Calibrar prensa", prioridad="alta")
        self.nueva_tarea("Limpiar bodega", prioridad="baja")
        r = self.client.get("/?q=prensa")
        txt = r.get_data(as_text=True)
        self.assertIn("Calibrar prensa", txt)
        self.assertNotIn("Limpiar bodega", txt)
        r = self.client.get("/?prioridad=baja")
        txt = r.get_data(as_text=True)
        self.assertIn("Limpiar bodega", txt)
        self.assertNotIn("Calibrar prensa", txt)

    def test_cp10_marcar_completada_y_filtrar(self):
        self.nueva_tarea("Inspección final")
        self.client.post("/tareas/1/estado")
        txt = self.client.get("/?estado=completada").get_data(as_text=True)
        self.assertIn("Inspección final", txt)
        txt = self.client.get("/?estado=pendiente").get_data(as_text=True)
        self.assertNotIn("Inspección final", txt)

    def test_tarea_inexistente_da_404(self):
        self.assertEqual(self.client.get("/tareas/99/editar").status_code, 404)


class TestAutorizacion(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.crear_usuario_y_entrar()      # Ana, id=1
        self.otro = self.segundo_cliente()  # Luis, id=2
        self.nueva_tarea("Tarea privada de Ana", asignado_id=1)

    def test_cp05_usuario_no_ve_tareas_ajenas(self):
        txt = self.otro.get("/").get_data(as_text=True)
        self.assertNotIn("Tarea privada de Ana", txt)

    def test_cp05_usuario_no_puede_editar_tarea_ajena(self):
        self.assertEqual(self.otro.get("/tareas/1/editar").status_code, 403)

    def test_cp05_usuario_no_puede_eliminar_tarea_ajena(self):
        self.assertEqual(self.otro.post("/tareas/1/eliminar").status_code, 403)

    def test_cp05_usuario_no_puede_cambiar_estado_de_tarea_ajena(self):
        self.assertEqual(self.otro.post("/tareas/1/estado").status_code, 403)

    def test_asignado_puede_completar_pero_no_editar(self):
        self.nueva_tarea("Para Luis", asignado_id=2)  # id=2
        self.assertEqual(self.otro.post("/tareas/2/estado").status_code, 302)
        self.assertEqual(self.otro.get("/tareas/2/editar").status_code, 403)


class TestPerfil(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.crear_usuario_y_entrar()

    def test_cp11_editar_perfil(self):
        r = self.client.post("/perfil", data={
            "nombre": "Ana María", "email": "ana@empresa.com"},
            follow_redirects=True)
        self.assertIn("Perfil actualizado", r.get_data(as_text=True))
        self.assertIn("Ana María", r.get_data(as_text=True))

    def test_cp11_cambiar_password_y_login(self):
        r = self.client.post("/perfil/password", data={
            "actual": "Clave1234", "nueva": "NuevaClave99"},
            follow_redirects=True)
        self.assertIn("Contraseña actualizada", r.get_data(as_text=True))
        self.client.get("/logout")
        r = self.login(password="NuevaClave99")
        self.assertIn("Mis tareas", r.get_data(as_text=True))

    def test_cambiar_password_actual_incorrecta(self):
        r = self.client.post("/perfil/password", data={
            "actual": "Mala12345", "nueva": "NuevaClave99"},
            follow_redirects=True)
        self.assertIn("actual es incorrecta", r.get_data(as_text=True))

    def test_correo_duplicado_en_perfil(self):
        self.segundo_cliente()
        r = self.client.post("/perfil", data={
            "nombre": "Ana", "email": "luis@empresa.com"},
            follow_redirects=True)
        self.assertIn("ya está en uso", r.get_data(as_text=True))
