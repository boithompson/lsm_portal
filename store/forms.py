from django import forms
from .models import Inventory, SalesRecord, SalesItem, Branch
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        exclude = ["added_on"]
        widgets = {
            "vehicle_type": forms.Select(attrs={"class": "form-select"}),
            "make": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "vin": forms.TextInput(attrs={"class": "form-control"}),
            "color": forms.TextInput(attrs={"class": "form-control"}),
            "mileage": forms.NumberInput(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # Pass the request.user when initializing
        super().__init__(*args, **kwargs)

        # Style branch field even if hidden later
        self.fields["branch"].widget.attrs["class"] = "form-select"

        if user and user.access_level != "admin":
            # Hide the branch field for non-admins (set it in the view)
            self.fields["branch"].widget = forms.HiddenInput()
        else:
            # Admin can select the branch
            self.fields["branch"].queryset = Branch.objects.all()


class SalesRecordForm(forms.ModelForm):
    marketer = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = SalesRecord
        fields = [
            "customer_name",
            "customer_contact",
            "marketer",
            "amount_paid_cash",
            "credit_owed",
        ]
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "customer_contact": forms.TextInput(attrs={"class": "form-control"}),
            "amount_paid_cash": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "credit_owed": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }


class SalesItemForm(forms.ModelForm):
    vin = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = SalesItem
        fields = ["vin", "price_at_sale"]  # Changed from inventory_item to vin
        widgets = {
            "price_at_sale": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }

    def clean_vin(self):
        vin = self.cleaned_data["vin"]
        try:
            inventory_item = Inventory.objects.get(vin=vin)
            if inventory_item.status != "available":
                raise ValidationError(
                    f"Vehicle with VIN {vin} is not available for sale (status: {inventory_item.status})."
                )
        except Inventory.DoesNotExist:
            raise ValidationError(f"No inventory item found with VIN: {vin}.")
        return vin

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the inventory_item field from the base fields as it's replaced by vin
        self.fields.pop("inventory_item", None)
        # Add the custom vin field back
        self.fields["vin"] = self.base_fields["vin"]


SalesItemFormSet = inlineformset_factory(
    SalesRecord, SalesItem, form=SalesItemForm, extra=1, can_delete=True
)
