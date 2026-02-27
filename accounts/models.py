import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.urls import reverse


def generate_unique_id():
    return str(uuid.uuid4())[:9]


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("access_level", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class CustomUser(AbstractBaseUser):
    class AccessLevel(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        ACCOUNT = "account", "Account"
        PROCUREMENT = "procurement", "Procurement"
        WORKSHOP = "workshop", "Workshop"
        SALES = "sales", "Sales"

    unique_id = models.CharField(
        max_length=9, unique=True, default=generate_unique_id, editable=False
    )
    access_level = models.CharField(
        max_length=20, choices=AccessLevel.choices, default=AccessLevel.WORKSHOP
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    branch = models.ForeignKey(
        "Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="users"
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.full_name

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Branch-specific signatory fields for invoices
    workshop_manager_name = models.CharField(max_length=255, blank=True, null=True)
    service_advisor_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url_for_sales_list(self):
        return reverse(
            "store:sales_list_by_branch_filter", kwargs={"branch_pk": self.pk}
        )
