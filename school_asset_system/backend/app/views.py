from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import (
    Building, Room, AssetType, Asset, Equipment, Furniture,
    Electronics, InventoryItem, Maintenance, Transfer, WriteOff, Notification, AuditLog
)
from .serializers import (
    UserSerializer, UserCreateSerializer, BuildingSerializer, RoomSerializer,
    AssetTypeSerializer, AssetSerializer, EquipmentSerializer, FurnitureSerializer,
    ElectronicsSerializer, InventoryItemSerializer, MaintenanceSerializer,
    TransferSerializer, WriteOffSerializer, NotificationSerializer, AuditLogSerializer
)

User = get_user_model()


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrResponsible(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'material_responsible']


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        role = request.query_params.get('role')
        if role:
            users = User.objects.filter(role=role)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        return Response({'error': 'Роль не указана'}, status=status.HTTP_400_BAD_REQUEST)


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'address']


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('building', 'parent').all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['building', 'floor']
    search_fields = ['number', 'name']
    ordering_fields = ['floor', 'number']
    
    @action(detail=True, methods=['get'])
    def assets(self, request, pk=None):
        room = self.get_object()
        assets = Asset.objects.filter(room=room)
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)


class AssetTypeViewSet(viewsets.ModelViewSet):
    queryset = AssetType.objects.all()
    serializer_class = AssetTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related('asset_type', 'room', 'responsible').all()
    permission_classes = [IsAdminOrResponsible]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asset_type', 'status', 'room', 'responsible']
    search_fields = ['inventory_number', 'name', 'model', 'manufacturer', 'barcode']
    ordering_fields = ['created_at', 'purchase_date', 'inventory_number']
    
    def get_serializer_class(self):
        asset_type = self.request.query_params.get('asset_type')
        if asset_type:
            try:
                type_obj = AssetType.objects.get(pk=asset_type)
                if type_obj.category == 'equipment':
                    return EquipmentSerializer
                elif type_obj.category == 'furniture':
                    return FurnitureSerializer
                elif type_obj.category == 'electronics':
                    return ElectronicsSerializer
                elif type_obj.category == 'inventory':
                    return InventoryItemSerializer
            except AssetType.DoesNotExist:
                pass
        return AssetSerializer
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        asset = self.get_object()
        to_room_id = request.data.get('to_room')
        to_responsible_id = request.data.get('to_responsible')
        reason = request.data.get('reason', '')
        
        if not to_room_id:
            return Response({'error': 'Не указано помещение'}, status=status.HTTP_400_BAD_REQUEST)
        
        transfer = Transfer.objects.create(
            asset=asset,
            from_room=asset.room,
            to_room_id=to_room_id,
            from_responsible=asset.responsible,
            to_responsible_id=to_responsible_id,
            reason=reason
        )
        
        asset.room_id = to_room_id
        asset.responsible_id = to_responsible_id
        asset.save()
        
        # Создание уведомления
        if to_responsible_id:
            Notification.objects.create(
                user_id=to_responsible_id,
                notification_type='critical',
                title='Новое имущество закреплено',
                message=f'Имущество {asset.inventory_number} закреплено за вами'
            )
        
        serializer = TransferSerializer(transfer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_maintenance(self, request, pk=None):
        asset = self.get_object()
        maintenance = Maintenance.objects.create(
            asset=asset,
            maintenance_type=request.data.get('maintenance_type'),
            description=request.data.get('description', ''),
            cost=request.data.get('cost'),
            performed_by=request.data.get('performed_by', ''),
            next_date=request.data.get('next_date')
        )
        serializer = MaintenanceSerializer(maintenance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def warranty_expiring(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date() + timedelta(days=days)
        assets = Asset.objects.filter(warranty_end__lte=end_date, warranty_end__gte=timezone.now().date())
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = {
            'total': Asset.objects.count(),
            'by_status': {},
            'by_category': {},
            'warranty_expiring_soon': Asset.objects.filter(
                warranty_end__lte=timezone.now().date() + timedelta(days=30),
                warranty_end__gte=timezone.now().date()
            ).count(),
        }
        
        for status_key, status_label in Asset.STATUS_CHOICES:
            stats['by_status'][status_key] = Asset.objects.filter(status=status_key).count()
        
        for asset_type in AssetType.objects.all():
            stats['by_category'][asset_type.name] = Asset.objects.filter(asset_type=asset_type).count()
        
        return Response(stats)


class EquipmentViewSet(AssetViewSet):
    queryset = Equipment.objects.select_related('asset_type', 'room', 'responsible').all()
    serializer_class = EquipmentSerializer


class FurnitureViewSet(AssetViewSet):
    queryset = Furniture.objects.select_related('asset_type', 'room', 'responsible').all()
    serializer_class = FurnitureSerializer


class ElectronicsViewSet(AssetViewSet):
    queryset = Electronics.objects.select_related('asset_type', 'room', 'responsible').all()
    serializer_class = ElectronicsSerializer


class InventoryItemViewSet(AssetViewSet):
    queryset = InventoryItem.objects.select_related('asset_type', 'room', 'responsible').all()
    serializer_class = InventoryItemSerializer


class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.select_related('asset').all()
    serializer_class = MaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['asset', 'maintenance_type']
    ordering_fields = ['date_performed', 'next_date']
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        today = timezone.now().date()
        maintenances = Maintenance.objects.filter(
            next_date__gte=today,
            next_date__lte=today + timedelta(days=30)
        )
        serializer = MaintenanceSerializer(maintenances, many=True)
        return Response(serializer.data)


class TransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.select_related('asset', 'from_room', 'to_room', 'from_responsible', 'to_responsible').all()
    serializer_class = TransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['asset', 'from_room', 'to_room', 'to_responsible']
    ordering_fields = ['transfer_date']


class WriteOffViewSet(viewsets.ModelViewSet):
    queryset = WriteOff.objects.select_related('asset').all()
    serializer_class = WriteOffSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['reason']
    ordering_fields = ['act_date']


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.none()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'Прочитано'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'Все прочитано'})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'model_name']
    ordering_fields = ['timestamp']
