from django.db import models
from accounts.models import Branch
import uuid


class Inventory(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ("car", "Car"),
        ("truck", "Truck"),
        ("bus", "Bus"),
        ("van", "Van"),
        ("suv", "SUV"),
        ("motorcycle", "Motorcycle"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("available", "Available"),
        ("sold", "Sold"),
        ("reserved", "Reserved"),
        ("maintenance", "Under Maintenance"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="inventories"
    )
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    make = models.CharField(max_length=100)  # e.g., Toyota, Ford
    model = models.CharField(max_length=100)  # e.g., Camry, Ranger
    year = models.PositiveIntegerField()
    vin = models.CharField("Chassis/VIN", max_length=100, unique=True)
    color = models.CharField(max_length=50)
    mileage = models.PositiveIntegerField()
    image = models.ImageField(upload_to="inventory_images/", blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="available"
    )
    added_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-added_on"]

    def __str__(self):
        return f"{self.make} {self.model} ({self.year}) - {self.branch.name}"
