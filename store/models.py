from django.db import models
from accounts.models import Branch
from django.contrib.auth import get_user_model  # Recommended way to get the User model

User = get_user_model()
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

    def save(self, *args, **kwargs):
        if not self._state.adding:  # if object already exists (not being added for the first time)
            original_inventory = Inventory.objects.get(pk=self.pk)
            if original_inventory.status == "sold" and self.status != "sold":
                # If it was sold, and now trying to change to something else, prevent it
                raise ValueError("Cannot change status of a sold item.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.make} {self.model} ({self.year}) - {self.branch.name}"


class SalesRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="sales_records"
    )
    customer_name = models.CharField(max_length=200)
    customer_contact = models.CharField(max_length=200, blank=True, null=True)
    marketer = models.CharField(
        max_length=200, blank=True, null=True
    )  # Changed to CharField
    sale_date = models.DateTimeField(auto_now_add=True)
    amount_paid_cash = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    credit_owed = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )  # Changed from credit_owed
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )  # This will be calculated

    class Meta:
        ordering = ["-sale_date"]

    def __str__(self):
        return f"Sale to {self.customer_name} at {self.branch.name} on {self.sale_date.strftime('%Y-%m-%d')}"


class SalesItem(models.Model):
    sales_record = models.ForeignKey(
        SalesRecord, on_delete=models.CASCADE, related_name="items"
    )
    inventory_item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    price_at_sale = models.DecimalField(
        max_digits=12, decimal_places=2
    )  # Price of the item at the time of sale

    def __str__(self):
        return f"{self.inventory_item.make} {self.inventory_item.model} for Sale {self.sales_record.id}"
