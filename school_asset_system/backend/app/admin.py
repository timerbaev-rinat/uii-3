from django.contrib import admin
from .models import (
    User, Building, Room, AssetType, Asset, Equipment, Furniture,
    Electronics, InventoryItem, Maintenance, Transfer, WriteOff, Notification, AuditLog
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'position', 'phone']
    list_filter = ['role']
    search_fields = ['username', 'email', 'last_name', 'first_name']


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'address']
    search_fields = ['name', 'address']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['number', 'building', 'floor', 'name']
    list_filter = ['building', 'floor']
    search_fields = ['number', 'name']


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['inventory_number', 'name', 'asset_type', 'room', 'responsible', 'status']
    list_filter = ['asset_type', 'status', 'room']
    search_fields = ['inventory_number', 'name', 'model', 'manufacturer', 'barcode']
    readonly_fields = ['qr_code', 'created_at', 'updated_at']


@admin.register(Equipment)
class EquipmentAdmin(AssetAdmin):
    pass


@admin.register(Furniture)
class FurnitureAdmin(AssetAdmin):
    pass


@admin.register(Electronics)
class ElectronicsAdmin(AssetAdmin):
    pass


@admin.register(InventoryItem)
class InventoryItemAdmin(AssetAdmin):
    pass


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ['asset', 'maintenance_type', 'date_performed', 'cost']
    list_filter = ['maintenance_type']
    search_fields = ['asset__inventory_number', 'description']


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['asset', 'from_room', 'to_room', 'transfer_date']
    list_filter = ['transfer_date']
    search_fields = ['asset__inventory_number']


@admin.register(WriteOff)
class WriteOffAdmin(admin.ModelAdmin):
    list_display = ['asset', 'reason', 'act_number', 'act_date']
    list_filter = ['reason', 'act_date']
    search_fields = ['asset__inventory_number', 'act_number']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'timestamp']
    list_filter = ['action', 'model_name']
    search_fields = ['object_repr']
