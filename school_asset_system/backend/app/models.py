from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Пользователь с ролями"""
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('material_responsible', 'Материально ответственное лицо'),
        ('employee', 'Сотрудник'),
        ('pedagog', 'Педагог'),
        ('accountant', 'Бухгалтер'),
        ('tech_specialist', 'Технический специалист'),
    ]
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='employee')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    position = models.CharField('Должность', max_length=100, blank=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='app_user_groups',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='app_user_permissions',
        related_query_name='user',
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Building(models.Model):
    """Корпус/Здание"""
    name = models.CharField('Название', max_length=100)
    address = models.CharField('Адрес', max_length=255)
    
    class Meta:
        verbose_name = 'Корпус'
        verbose_name_plural = 'Корпуса'
    
    def __str__(self):
        return self.name


class Room(models.Model):
    """Помещение с иерархией"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, verbose_name='Корпус')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                               verbose_name='Родительское помещение')
    number = models.CharField('Номер', max_length=20)
    name = models.CharField('Название', max_length=100, blank=True)
    floor = models.IntegerField('Этаж', default=1)
    area = models.DecimalField('Площадь (м²)', max_digits=8, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Помещение'
        verbose_name_plural = 'Помещения'
        ordering = ['building', 'floor', 'number']
    
    def __str__(self):
        return f'{self.building} - {self.number}'


class AssetType(models.Model):
    """Тип имущества"""
    CATEGORY_CHOICES = [
        ('equipment', 'Оборудование'),
        ('furniture', 'Мебель'),
        ('electronics', 'Электроника'),
        ('inventory', 'Инвентарь'),
        ('other', 'Прочее'),
    ]
    
    name = models.CharField('Название', max_length=100)
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField('Описание', blank=True)
    
    class Meta:
        verbose_name = 'Тип имущества'
        verbose_name_plural = 'Типы имущества'
    
    def __str__(self):
        return self.name


class Asset(models.Model):
    """Основная модель имущества"""
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('in_use', 'В эксплуатации'),
        ('repair', 'В ремонте'),
        ('write_off', 'Списано'),
        ('lost', 'Утеряно'),
        ('archived', 'Архивировано'),
    ]
    
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT, verbose_name='Тип')
    inventory_number = models.CharField('Инвентарный номер', max_length=50, unique=True)
    barcode = models.CharField('Штрихкод', max_length=100, unique=True, blank=True)
    qr_code = models.ImageField('QR-код', upload_to='qr_codes/', blank=True, null=True)
    
    name = models.CharField('Наименование', max_length=200)
    model = models.CharField('Модель', max_length=100, blank=True)
    manufacturer = models.CharField('Производитель', max_length=100, blank=True)
    serial_number = models.CharField('Серийный номер', max_length=100, blank=True)
    
    purchase_date = models.DateField('Дата приобретения', null=True, blank=True)
    purchase_price = models.DecimalField('Цена приобретения', max_digits=12, decimal_places=2, null=True, blank=True)
    warranty_end = models.DateField('Гарантия до', null=True, blank=True)
    
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Помещение')
    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    verbose_name='Ответственное лицо', related_name='responsible_assets')
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField('Примечание', blank=True)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Имущество'
        verbose_name_plural = 'Имущество'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f'{self.inventory_number} - {self.name}'
    
    def is_warranty_expiring_soon(self, days=30):
        """Проверка окончания гарантии"""
        if self.warranty_end:
            return self.warranty_end <= timezone.now().date() + timedelta(days=days)
        return False


class Equipment(Asset):
    """Оборудование - специфичные поля"""
    power = models.CharField('Мощность', max_length=50, blank=True)
    voltage = models.CharField('Напряжение', max_length=50, blank=True)
    dimensions = models.CharField('Габариты', max_length=100, blank=True)
    weight = models.DecimalField('Вес (кг)', max_digits=8, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Оборудование'
        verbose_name_plural = 'Оборудование'


class Furniture(Asset):
    """Мебель - специфичные поля"""
    material = models.CharField('Материал', max_length=100, blank=True)
    color = models.CharField('Цвет', max_length=50, blank=True)
    dimensions = models.CharField('Габариты', max_length=100, blank=True)
    seats_count = models.IntegerField('Количество мест', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Мебель'
        verbose_name_plural = 'Мебель'


class Electronics(Asset):
    """Электроника - специфичные поля"""
    cpu = models.CharField('Процессор', max_length=100, blank=True)
    ram = models.CharField('ОЗУ', max_length=50, blank=True)
    storage = models.CharField('Накопитель', max_length=100, blank=True)
    screen_size = models.CharField('Размер экрана', max_length=20, blank=True)
    os = models.CharField('ОС', max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'Электроника'
        verbose_name_plural = 'Электроника'


class InventoryItem(Asset):
    """Инвентарь - специфичные поля"""
    quantity = models.IntegerField('Количество', default=1)
    unit = models.CharField('Ед. измерения', max_length=20, default='шт')
    
    class Meta:
        verbose_name = 'Инвентарь'
        verbose_name_plural = 'Инвентарь'


class Maintenance(models.Model):
    """Обслуживание и ремонт"""
    TYPE_CHOICES = [
        ('maintenance', 'Плановое обслуживание'),
        ('repair', 'Ремонт'),
        ('inspection', 'Проверка'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name='Имущество', related_name='maintenances')
    maintenance_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES)
    description = models.TextField('Описание')
    cost = models.DecimalField('Стоимость', max_digits=10, decimal_places=2, null=True, blank=True)
    performed_by = models.CharField('Выполнено', max_length=200, blank=True)
    date_performed = models.DateField('Дата выполнения', default=timezone.now)
    next_date = models.DateField('Следующее обслуживание', null=True, blank=True)
    document = models.FileField('Документ', upload_to='maintenance_docs/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Обслуживание'
        verbose_name_plural = 'Обслуживания'
        ordering = ['-date_performed']


class Transfer(models.Model):
    """Перемещение имущества"""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, verbose_name='Имущество', related_name='transfers')
    from_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, 
                                  verbose_name='Из помещения', related_name='transfers_from')
    to_room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name='В помещение', related_name='transfers_to')
    from_responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         verbose_name='От ответственного', related_name='transfers_from')
    to_responsible = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='К ответственному',
                                       related_name='transfers_to')
    transfer_date = models.DateTimeField('Дата перемещения', default=timezone.now)
    reason = models.TextField('Причина', blank=True)
    act_number = models.CharField('Номер акта', max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'Перемещение'
        verbose_name_plural = 'Перемещения'
        ordering = ['-transfer_date']


class WriteOff(models.Model):
    """Списание имущества"""
    REASON_CHOICES = [
        ('wear', 'Износ'),
        ('damage', 'Повреждение'),
        ('loss', 'Утрата'),
        ('theft', 'Кража'),
        ('other', 'Прочее'),
    ]
    
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, verbose_name='Имущество')
    reason = models.CharField('Причина', max_length=20, choices=REASON_CHOICES)
    description = models.TextField('Описание причины')
    commission_members = models.TextField('Члены комиссии')
    act_number = models.CharField('Номер акта', max_length=50)
    act_date = models.DateField('Дата акта', default=timezone.now)
    act_document = models.FileField('Акт списания', upload_to='writeoff_acts/')
    
    class Meta:
        verbose_name = 'Списание'
        verbose_name_plural = 'Списания'
        ordering = ['-act_date']


class Notification(models.Model):
    """Уведомления"""
    TYPE_CHOICES = [
        ('warranty', 'Окончание гарантии'),
        ('maintenance', 'Плановое обслуживание'),
        ('inventory', 'Инвентаризация'),
        ('critical', 'Критическое событие'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    notification_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES)
    title = models.CharField('Заголовок', max_length=200)
    message = models.TextField('Сообщение')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']


class AuditLog(models.Model):
    """Журнал аудита"""
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Изменение'),
        ('delete', 'Удаление'),
        ('transfer', 'Перемещение'),
        ('writeoff', 'Списание'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Пользователь')
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField('Модель', max_length=50)
    object_id = models.PositiveIntegerField('ID объекта')
    object_repr = models.CharField('Представление', max_length=200)
    changes = models.JSONField('Изменения', blank=True, null=True)
    timestamp = models.DateTimeField('Время', auto_now_add=True)
    ip_address = models.GenericIPAddressField('IP адрес', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Лог аудита'
        verbose_name_plural = 'Логи аудита'
        ordering = ['-timestamp']
