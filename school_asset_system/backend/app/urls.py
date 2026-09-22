from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, BuildingViewSet, RoomViewSet, AssetTypeViewSet,
    AssetViewSet, EquipmentViewSet, FurnitureViewSet, ElectronicsViewSet,
    InventoryItemViewSet, MaintenanceViewSet, TransferViewSet,
    WriteOffViewSet, NotificationViewSet, AuditLogViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'buildings', BuildingViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'asset-types', AssetTypeViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'furniture', FurnitureViewSet)
router.register(r'electronics', ElectronicsViewSet)
router.register(r'inventory', InventoryItemViewSet)
router.register(r'maintenance', MaintenanceViewSet)
router.register(r'transfers', TransferViewSet)
router.register(r'writeoffs', WriteOffViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),
]
