from django.db import migrations, models


def transfer_to_bank_transfer(apps, schema_editor):
    Transaction = apps.get_model('finanzas', 'Transaction')
    Transaction.objects.filter(payment_method='TRANSFER').update(payment_method='BANK_TRANSFER')


def bank_transfer_to_transfer(apps, schema_editor):
    Transaction = apps.get_model('finanzas', 'Transaction')
    Transaction.objects.filter(payment_method='BANK_TRANSFER').update(payment_method='TRANSFER')


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas', '0004_transaction_ip_address_transaction_user_agent_and_more'),
    ]

    operations = [
        migrations.RunPython(transfer_to_bank_transfer, bank_transfer_to_transfer),
        migrations.AlterField(
            model_name='transaction',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('CASH', 'Efectivo'),
                    ('BANK_TRANSFER', 'Transferencia'),
                    ('DEBIT_CARD', 'Tarjeta de Débito'),
                    ('CREDIT_CARD', 'Tarjeta de Crédito'),
                    ('MERCADOPAGO', 'MercadoPago'),
                    ('OTHER', 'Otro'),
                ],
                default='CASH',
                max_length=20,
            ),
        ),
    ]
