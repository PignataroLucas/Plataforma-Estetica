from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import (
    Cliente,
    CodigoInvitacion,
    HistorialCliente,
    NotaCliente,
    PlanTratamiento,
    RutinaCuidado,
    UsuarioCliente,
    VinculacionCliente,
)
from apps.clientes.services import fusionar_clientes
from apps.empleados.models import CentroEstetica


class FusionarClientesTests(TestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(
            nombre='Centro', telefono='111', email='c@c.com'
        )
        self.otro_centro = CentroEstetica.objects.create(
            nombre='Otro', telefono='222', email='o@o.com'
        )
        self.principal = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Maria', apellido='Lopez', telefono='1150510001',
        )
        self.duplicado = Cliente.objects.create(
            centro_estetica=self.centro, nombre='Maria', apellido='Lopez', telefono='1150510001',
        )

    def _cargar_relaciones(self, cliente):
        HistorialCliente.objects.create(cliente=cliente, fecha=timezone.now())
        PlanTratamiento.objects.create(cliente=cliente, tratamiento_sugerido='Plan X')
        RutinaCuidado.objects.create(cliente=cliente, activa=True)
        NotaCliente.objects.create(cliente=cliente, contenido='una nota')
        CodigoInvitacion.objects.create(cliente=cliente)

    def test_reasigna_relaciones_y_borra_duplicado(self):
        self._cargar_relaciones(self.duplicado)
        dup_id = self.duplicado.id

        fusionar_clientes(self.principal, self.duplicado)

        # La ficha duplicada ya no existe
        self.assertFalse(Cliente.objects.filter(pk=dup_id).exists())
        # Todo colgado ahora de la principal
        self.assertEqual(self.principal.historial.count(), 1)
        self.assertEqual(self.principal.planes_tratamiento.count(), 1)
        self.assertEqual(self.principal.rutinas_cuidado.count(), 1)
        self.assertEqual(self.principal.notas.count(), 1)
        self.assertEqual(self.principal.codigos_invitacion.count(), 1)

    def test_vinculaciones_reasignadas_y_deduplicadas(self):
        u_compartido = UsuarioCliente.objects.create_user(email='c@mail.com', password='ClaveSegura123')
        u_solo_dup = UsuarioCliente.objects.create_user(email='d@mail.com', password='ClaveSegura123')
        # u_compartido está vinculado a AMBAS fichas
        VinculacionCliente.objects.create(
            usuario_cliente=u_compartido, cliente=self.principal,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )
        VinculacionCliente.objects.create(
            usuario_cliente=u_compartido, cliente=self.duplicado,
            metodo_vinculacion=VinculacionCliente.Metodo.CODIGO_INVITACION,
        )
        # u_solo_dup solo a la duplicada
        VinculacionCliente.objects.create(
            usuario_cliente=u_solo_dup, cliente=self.duplicado,
            metodo_vinculacion=VinculacionCliente.Metodo.REGISTRO_NUEVO,
        )

        fusionar_clientes(self.principal, self.duplicado)

        usuarios = set(self.principal.vinculaciones.values_list('usuario_cliente_id', flat=True))
        self.assertEqual(usuarios, {u_compartido.id, u_solo_dup.id})
        # No quedó vínculo duplicado del usuario compartido
        self.assertEqual(
            self.principal.vinculaciones.filter(usuario_cliente=u_compartido).count(), 1
        )

    def test_consolida_campos_sin_pisar_y_or_de_flags(self):
        self.principal.email = ''
        self.principal.direccion = 'Calle Principal'
        self.principal.cancer_historial = False
        self.principal.save()

        self.duplicado.email = 'recuperado@mail.com'
        self.duplicado.direccion = 'Otra Calle'
        self.duplicado.cancer_historial = True  # advertencia médica en la duplicada
        self.duplicado.save()

        fusionar_clientes(self.principal, self.duplicado)
        self.principal.refresh_from_db()

        self.assertEqual(self.principal.email, 'recuperado@mail.com')  # completó el vacío
        self.assertEqual(self.principal.direccion, 'Calle Principal')  # NO pisó lo existente
        self.assertTrue(self.principal.cancer_historial)  # OR conservó la advertencia

    def test_no_permite_misma_ficha(self):
        with self.assertRaises(ValueError):
            fusionar_clientes(self.principal, self.principal)

    def test_no_permite_distinto_centro(self):
        ajeno = Cliente.objects.create(
            centro_estetica=self.otro_centro, nombre='X', apellido='Y', telefono='9',
        )
        with self.assertRaises(ValueError):
            fusionar_clientes(self.principal, ajeno)
