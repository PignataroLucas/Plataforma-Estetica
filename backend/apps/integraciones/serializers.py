"""
Serializers for the Conto integration.

Two rules that are load-bearing rather than cosmetic:

- `center` is never accepted from the request. It comes from the authenticated
  user, so a payload cannot point an integration at another tenant.
- `token` is write-only. Once stored it is never returned by the API.
"""
from rest_framework import serializers

from apps.empleados.models import Sucursal

from .models import ContoIntegration, ContoSale


class ContoIntegrationSerializer(serializers.ModelSerializer):
    """Read and write the integration configuration."""

    token = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        help_text="Token de solo lectura generado en Conto. No se devuelve nunca"
    )
    token_configurado = serializers.SerializerMethodField()
    center_nombre = serializers.CharField(source='center.nombre', read_only=True)
    branch_nombre = serializers.CharField(source='branch.nombre', read_only=True)
    esta_vinculada = serializers.BooleanField(source='is_linked', read_only=True)
    puede_sincronizar = serializers.BooleanField(source='can_sync', read_only=True)

    class Meta:
        model = ContoIntegration
        fields = [
            'id',
            'center', 'center_nombre',
            'branch', 'branch_nombre',
            'base_url', 'token', 'token_configurado',
            'conto_account_id', 'conto_account_name', 'link_verified_at',
            'esta_vinculada', 'puede_sincronizar',
            'is_active',
            'default_payment_method', 'channels_to_import',
            'create_missing_clients', 'create_missing_products',
            'import_from', 'last_stock_sync', 'last_sales_sync',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            # Filled from the authenticated user, never from the payload.
            'center',
            # Filled by verifying against Conto, never typed.
            'conto_account_id', 'conto_account_name', 'link_verified_at',
            'last_stock_sync', 'last_sales_sync',
            'created_at', 'updated_at',
        ]

    def get_token_configurado(self, obj):
        """Lets the UI show whether a token exists without exposing it."""
        return bool(obj.token)

    def validate_branch(self, value):
        """
        The branch must belong to the requesting user's center.

        Without this, sending another center's branch id is enough to make the
        integration write stock and income into the wrong tenant.
        """
        user = self.context['request'].user
        if value.centro_estetica_id != user.centro_estetica_id:
            raise serializers.ValidationError(
                "La sucursal no pertenece a tu centro de estética"
            )
        return value

    def validate_channels_to_import(self, value):
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise serializers.ValidationError(
                "Debe ser una lista de nombres de canal"
            )
        if not value:
            raise serializers.ValidationError(
                "Elegí al menos un canal, o desactivá la integración"
            )
        return value

    def validate(self, attrs):
        """
        Turning the integration on requires a verified link.

        Only checked when the request actually sets `is_active` to True. An
        earlier version looked at the effective value, which blocked unrelated
        edits — including updating the token, which is how you would fix a
        broken link in the first place.

        Leaving the flag on without a verified link is not a hole: `can_sync`
        and the Celery tasks both require `link_verified_at`, so nothing syncs.
        """
        if attrs.get('is_active') is True:
            already_linked = self.instance.is_linked if self.instance else False
            if not already_linked:
                raise serializers.ValidationError({
                    'is_active': "Verificá la vinculación con Conto antes de activar"
                })

        return attrs


class ContoIntegrationCreateSerializer(ContoIntegrationSerializer):
    """On creation the token and base_url are mandatory."""

    token = serializers.CharField(write_only=True, required=True)

    class Meta(ContoIntegrationSerializer.Meta):
        pass

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get('base_url'):
            raise serializers.ValidationError({'base_url': "Requerido"})
        return attrs


class ContoSaleSerializer(serializers.ModelSerializer):
    """Read-only view of an imported voucher."""

    tipo_display = serializers.CharField(source='get_type_display', read_only=True)
    estado_display = serializers.CharField(source='get_status_display', read_only=True)
    cantidad_transacciones = serializers.SerializerMethodField()
    monto_transacciones = serializers.SerializerMethodField()

    class Meta:
        model = ContoSale
        fields = [
            'id', 'voucher_id', 'type', 'tipo_display',
            'related_voucher_id', 'external_order_id', 'channel',
            'date', 'total',
            'sale_origin', 'app_origin', 'coupon_code', 'coupon_discount',
            'status', 'estado_display', 'error_message',
            'cantidad_transacciones', 'monto_transacciones',
            'processed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_cantidad_transacciones(self, obj):
        return obj.transactions.count()

    def get_monto_transacciones(self, obj):
        return sum(t.amount for t in obj.transactions.all())


class ContoSaleDetailSerializer(ContoSaleSerializer):
    """Adds the raw payload, for diagnosing a voucher that failed."""

    class Meta(ContoSaleSerializer.Meta):
        fields = ContoSaleSerializer.Meta.fields + ['payload']
        read_only_fields = fields
