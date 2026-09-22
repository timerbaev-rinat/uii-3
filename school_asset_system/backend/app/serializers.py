from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Building, Room, AssetType, Asset, Equipment, Furniture, 
    Electronics, InventoryItem, Maintenance, Transfer, WriteOff, Notification, AuditLog
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'position']
        read_only_fields = ['id']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role', 'phone', 'position']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    parent_number = serializers.CharField(source='parent.number', read_only=True)
    
    class Meta:
        model = Room
        fields = '__all__'


class AssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetType
        fields = '__all__'


BASE_FIELDS = ['id', 'asset_type', 'asset_type_name', 'inventory_number', 'barcode', 'qr_code', 
               'name', 'model', 'manufacturer', 'serial_number', 'purchase_date', 'purchase_price',
               'warranty_end', 'room', 'room_number', 'building_name', 'responsible', 'responsible_name',
               'status', 'notes', 'created_at', 'updated_at', 'warranty_expiring']

class AssetSerializer(serializers.ModelSerializer):
    asset_type_name = serializers.CharField(source='asset_type.name', read_only=True)
    room_number = serializers.CharField(source='room.number', read_only=True)
    building_name = serializers.CharField(source='room.building.name', read_only=True)
    responsible_name = serializers.SerializerMethodField()
    warranty_expiring = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = BASE_FIELDS
        read_only_fields = ['barcode', 'qr_code', 'created_at', 'updated_at']
    
    def get_responsible_name(self, obj):
        if obj.responsible:
            return f'{obj.responsible.last_name} {obj.responsible.first_name}'
        return None
    
    def get_warranty_expiring(self, obj):
        return obj.is_warranty_expiring_soon()
    
    def create(self, validated_data):
        instance = super().create(validated_data)
        # Генерация штрихкода и QR-кода
        self.generate_codes(instance)
        return instance
    
    def generate_codes(self, asset):
        """Генерация штрихкода и QR-кода"""
        import barcode
        from barcode.writer import ImageWriter
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile
        
        # Генерация штрихкода
        if not asset.barcode:
            code = barcode.get('code128', asset.inventory_number, writer=ImageWriter())
            buffer = BytesIO()
            code.write(buffer)
            asset.barcode = asset.inventory_number
            asset.save(update_fields=['barcode'])
        
        # Генерация QR-кода
        if not asset.qr_code:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f'ASSET:{asset.inventory_number}')
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer)
            asset.qr_code.save(f'qr_{asset.inventory_number}.png', ContentFile(buffer.getvalue()), save=True)


class EquipmentSerializer(AssetSerializer):
    class Meta(AssetSerializer.Meta):
        model = Equipment
        fields = BASE_FIELDS + ['power', 'voltage', 'dimensions', 'weight']


class FurnitureSerializer(AssetSerializer):
    class Meta(AssetSerializer.Meta):
        model = Furniture
        fields = BASE_FIELDS + ['material', 'color', 'dimensions', 'seats_count']


class ElectronicsSerializer(AssetSerializer):
    class Meta(AssetSerializer.Meta):
        model = Electronics
        fields = BASE_FIELDS + ['cpu', 'ram', 'storage', 'screen_size', 'os']


class InventoryItemSerializer(AssetSerializer):
    class Meta(AssetSerializer.Meta):
        model = InventoryItem
        fields = BASE_FIELDS + ['quantity', 'unit']


class MaintenanceSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_inventory_number = serializers.CharField(source='asset.inventory_number', read_only=True)
    
    class Meta:
        model = Maintenance
        fields = '__all__'


class TransferSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_inventory_number = serializers.CharField(source='asset.inventory_number', read_only=True)
    from_room_number = serializers.CharField(source='from_room.number', read_only=True)
    to_room_number = serializers.CharField(source='to_room.number', read_only=True)
    from_responsible_name = serializers.SerializerMethodField()
    to_responsible_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Transfer
        fields = '__all__'
    
    def get_from_responsible_name(self, obj):
        if obj.from_responsible:
            return f'{obj.from_responsible.last_name} {obj.from_responsible.first_name}'
        return None
    
    def get_to_responsible_name(self, obj):
        return f'{obj.to_responsible.last_name} {obj.to_responsible.first_name}'


class WriteOffSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_inventory_number = serializers.CharField(source='asset.inventory_number', read_only=True)
    
    class Meta:
        model = WriteOff
        fields = '__all__'
        read_only_fields = ['act_date']


class NotificationSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['is_read', 'created_at']
    
    def get_user_name(self, obj):
        return f'{obj.user.last_name} {obj.user.first_name}'


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['timestamp']
    
    def get_user_name(self, obj):
        if obj.user:
            return f'{obj.user.last_name} {obj.user.first_name}'
        return 'Система'
