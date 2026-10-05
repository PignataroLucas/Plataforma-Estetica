"""
La bandeja del centro: los pedidos de turno que alguien tiene que resolver.

Es una tabla aparte del outbox de avisos a propósito —ver el docstring de
`NotificacionInterna` y APROBACION_TURNOS_SPEC.md §2.5—: `Aviso` entrega push a
una cuenta de clienta y se olvida; esto es durable, accionable y de una sucursal.

La entrega por mail va en la misma fila, con su estado y sus reintentos, porque
el aviso es un solo hecho que llega a dos lugares.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("turnos", "0003_aprobacion_de_pedidos"),
        ("empleados", "0005_sucursal_ventana_de_respuesta"),
        (
            "notificaciones",
            "0004_aviso_dispositivopush_preferencianotificacion_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificacionInterna",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("TURNO_SOLICITADO", "Pidieron un turno"),
                            ("TURNO_POR_VENCER", "Un pedido está por vencer"),
                        ],
                        max_length=20,
                    ),
                ),
                ("titulo", models.CharField(max_length=150)),
                ("cuerpo", models.TextField()),
                (
                    "datos",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Lo que el CRM necesita para armar el link y pintar la fila.",
                    ),
                ),
                (
                    "clave",
                    models.CharField(
                        help_text="Idempotencia: `turno:12:solicitado` entra una sola vez por más que el disparador corra de nuevo.",
                        max_length=120,
                        unique=True,
                    ),
                ),
                ("leida_en", models.DateTimeField(blank=True, null=True)),
                (
                    "email_estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente"),
                            ("ENVIADO", "Enviado"),
                            ("SIN_DESTINO", "Sin destinatario configurado"),
                            ("FALLIDO", "Fallido"),
                        ],
                        default="PENDIENTE",
                        max_length=15,
                    ),
                ),
                (
                    "email_destino",
                    models.EmailField(
                        blank=True,
                        help_text="Se congela al crear: si mañana cambia el destinatario, esta fila sigue diciendo a dónde se mandó.",
                        max_length=254,
                    ),
                ),
                ("email_intentos", models.PositiveSmallIntegerField(default=0)),
                ("email_error", models.TextField(blank=True)),
                ("email_enviado_en", models.DateTimeField(blank=True, null=True)),
                ("creada_en", models.DateTimeField(auto_now_add=True)),
                (
                    "leida_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notificaciones_internas_leidas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sucursal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notificaciones_internas",
                        to="empleados.sucursal",
                    ),
                ),
                (
                    "turno",
                    models.ForeignKey(
                        blank=True,
                        help_text="Lo accionable sale de su estado, no de un campo acá.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notificaciones_internas",
                        to="turnos.turno",
                    ),
                ),
            ],
            options={
                "verbose_name": "Notificación interna",
                "verbose_name_plural": "Notificaciones internas",
                "ordering": ["-creada_en"],
                "indexes": [
                    models.Index(
                        fields=["sucursal", "-creada_en"],
                        name="notificacio_sucursa_bf3eee_idx",
                    ),
                    models.Index(
                        fields=["email_estado", "email_intentos"],
                        name="notificacio_email_e_3da09f_idx",
                    ),
                ],
            },
        ),
    ]
