from django.db import models
from accounts.models import CustomUser, Branch
import uuid
from decimal import Decimal # Import Decimal for precise calculations


class Vehicle(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    uuid = models.CharField(max_length=12, unique=True, editable=False)
    image = models.ImageField(upload_to="vehicle_images/", blank=True, null=True)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="vehicles"
    )
    customer_name = models.CharField(max_length=255)
    address = models.CharField(max_length=225)
    phone = models.CharField(max_length=20)
    vehicle_make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    chasis_no = models.CharField(max_length=100)
    licence_plate = models.CharField(max_length=20)
    date_of_first_registration = models.DateField()
    mileage = models.CharField(max_length=50, blank=True, null=True)
    complaint = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.vehicle_make} {self.model} ({self.licence_plate})"

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())[:12]
        super().save(*args, **kwargs)


class JobSheet(models.Model):
    vehicle = models.OneToOneField(
        Vehicle, on_delete=models.CASCADE, related_name="job_sheet"
    )
    service_advisor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="advised_job_sheets",
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_job_sheets",
    )
    accessories = models.TextField(blank=True)
    job_description = models.TextField()

    def __str__(self):
        return f"Job Sheet for {self.vehicle}"


class InternalEstimate(models.Model):
    vehicle = models.OneToOneField(
        Vehicle, on_delete=models.CASCADE, related_name="internal_estimate"
    )
    apply_vat = models.BooleanField(default=False)
    is_invoice = models.BooleanField(default=False) # New field
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) # New field
    total_with_vat = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) # New field

    def __str__(self):
        return f"Internal Estimate for {self.vehicle}"

    @property
    def grand_total(self):
        total = 0
        # Ensure the instance is saved before accessing related objects
        if self.pk:
            for estimate_part in self.estimatepart_set.all():
                total += estimate_part.price * estimate_part.quantity
        return total

    def save(self, *args, **kwargs):
        # Only call super().save() here. VAT calculation will be handled by signals.
        super().save(*args, **kwargs)


class EstimatePart(models.Model):
    estimate = models.ForeignKey(InternalEstimate, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.name} for {self.estimate}"
