from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.clientes.models import Cliente, HistorialCliente
from apps.empleados.models import CentroEstetica, Usuario


class DuplicadosEndpointTests(APITestCase):
    def setUp(self):
        self.centro = CentroEstetica.objects.create(nombre='Centro', telefono='1', email='c@c.com')
        self.otro = CentroEstetica.objects.create(nombre='Otro', telefono='2', email='o@o.com')
        self.staff = Usuario.objects.create_user(
            username='staff', password='staffpass123',
            centro_estetica=self.centro, rol=Usuario.Rol.ADMIN,
        )
        self.client.force_authenticate(self.staff)

    def _cliente(self, nombre, email='', tel_norm=None):
        c = Cliente.objects.create(
            centro_estetica=self.centro, nombre=nombre, apellido='X', telefono='0', email=email,
        )
        if tel_norm is not None:
            Cliente.objects.filter(pk=c.pk).update(telefono_normalizado=tel_norm)
        return c

    def _ids(self, grupo):
        return {c['id'] for c in grupo['clientes']}

    def test_detecta_grupos_con_confianza(self):
        # A,B: mismo teléfono + mismo email -> ALTA
        a = self._cliente('A', email='mismo@x.com', tel_norm='+5491150510001')
        b = self._cliente('B', email='mismo@x.com', tel_norm='+5491150510001')
        # C,D: mismo teléfono, distinto email -> MEDIA
        c = self._cliente('C', email='c@x.com', tel_norm='+5491150510002')
        d = self._cliente('D', email='d@x.com', tel_norm='+5491150510002')
        # E,F: mismo email, sin teléfono -> MEDIA
        e = self._cliente('E', email='comparten@x.com', tel_norm='')
        f = self._cliente('F', email='comparten@x.com', tel_norm='')
        # G: único
        g = self._cliente('G', email='g@x.com', tel_norm='+5491150519999')

        resp = self.client.get(reverse('cliente-duplicados'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        grupos = resp.data['grupos']

        alta = [gr for gr in grupos if gr['confianza'] == 'ALTA']
        self.assertEqual(len(alta), 1)
        self.assertEqual(self._ids(alta[0]), {a.id, b.id})

        medias = {frozenset(self._ids(gr)) for gr in grupos if gr['confianza'] == 'MEDIA'}
        self.assertIn(frozenset({c.id, d.id}), medias)
        self.assertIn(frozenset({e.id, f.id}), medias)

        # G no aparece en ningún grupo
        todos = set().union(*[self._ids(gr) for gr in grupos])
        self.assertNotIn(g.id, todos)

    def test_fusionar_endpoint(self):
        principal = self._cliente('Maria', email='m@x.com', tel_norm='+5491150510010')
        duplicado = self._cliente('Maria', email='m@x.com', tel_norm='+5491150510010')
        HistorialCliente.objects.create(cliente=duplicado, fecha=timezone.now())

        resp = self.client.post(
            reverse('cliente-fusionar'),
            {'principal': principal.id, 'duplicados': [duplicado.id]},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(Cliente.objects.filter(pk=duplicado.id).exists())
        self.assertEqual(principal.historial.count(), 1)

    def test_fusionar_bloquea_otro_centro(self):
        principal = self._cliente('Maria', tel_norm='+5491150510020')
        ajeno = Cliente.objects.create(
            centro_estetica=self.otro, nombre='Ajeno', apellido='Z', telefono='9',
        )
        resp = self.client.post(
            reverse('cliente-fusionar'),
            {'principal': principal.id, 'duplicados': [ajeno.id]},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        # La ficha ajena sigue intacta
        self.assertTrue(Cliente.objects.filter(pk=ajeno.id).exists())

    def test_requiere_auth(self):
        self.client.force_authenticate(None)
        resp = self.client.get(reverse('cliente-duplicados'))
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
