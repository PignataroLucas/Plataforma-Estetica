from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("servicios", "0001_initial"),
        ("finanzas", "0005_rename_transfer_to_bank_transfer"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="service",
            field=models.ForeignKey(
                blank=True,
                help_text="Servicio asociado (para servicios directos o turnos cobrados)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="transactions",
                to="servicios.servicio",
            ),
        ),
    ]
