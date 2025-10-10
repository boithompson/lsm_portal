from django.db import models
from accounts.models import Branch
from django.contrib.auth import get_user_model  # Recommended way to get the User model

User = get_user_model()
import uuid


class Stock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="stock_items"
    )
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    unit_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Stock"

    def __str__(self):
        return f"{self.name} ({self.quantity}) - {self.branch.name}"


class SalesRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="sales_records"
    )
    customer_name = models.CharField(max_length=200)
    customer_contact = models.CharField(max_length=200, blank=True, null=True)
    marketer = models.CharField(max_length=200, blank=True, null=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    amount_paid_cash = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    credit_owed = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bank_paid = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ["-sale_date"]

    def __str__(self):
        return f"Sale to {self.customer_name} at {self.branch.name} on {self.sale_date.strftime('%Y-%m-%d')}"


class SalesItem(models.Model):
    sales_record = models.ForeignKey(
        SalesRecord, on_delete=models.CASCADE, related_name="items"
    )
    stock_item = models.ForeignKey(
        Stock, on_delete=models.CASCADE, null=True, blank=True
    )
    quantity_sold = models.IntegerField(default=1)
    price_at_sale = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.pk is None:  # Only deduct stock for new sales items
            if self.stock_item.quantity < self.quantity_sold:
                raise ValueError("Not enough stock available.")
            self.stock_item.quantity -= self.quantity_sold
            self.stock_item.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.stock_item.name} (x{self.quantity_sold}) for Sale {self.sales_record.id}"
