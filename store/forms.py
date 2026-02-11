from django import forms
from .models import Stock, SalesRecord, SalesItem
from accounts.models import Branch  # Ensure Branch is imported from accounts.models
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.db import transaction


class StockForm(forms.ModelForm):
    unit_value = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )

    class Meta:
        model = Stock
        fields = ["name", "quantity", "unit_value", "branch"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["branch"].widget.attrs["class"] = "form-select"

        if user and user.access_level != "admin":
            self.fields["branch"].widget = forms.HiddenInput()
        else:
            self.fields["branch"].queryset = Branch.objects.all()


class CentralStockForm(forms.Form):
    name = forms.CharField(
        max_length=255, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    unit_value = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.branches = Branch.objects.all().order_by("name")
        for branch in self.branches:
            field_name = f"quantity_branch_{branch.id}"
            self.fields[field_name] = forms.IntegerField(
                required=False,
                min_value=0,
                widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
                label=f"Quantity for {branch.name}",
            )
            # If editing an existing stock item, pre-populate quantities
            if self.initial.get("stock_item_id"):
                stock_item = Stock.objects.filter(
                    name=self.initial["name"], branch=branch
                ).first()
                if stock_item:
                    self.initial[field_name] = stock_item.quantity

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        unit_value = cleaned_data.get("unit_value")

        if not name:
            raise ValidationError("Stock name is required.")

        # Check if at least one quantity is provided
        any_quantity_provided = False
        for branch in self.branches:
            field_name = f"quantity_branch_{branch.id}"
            if cleaned_data.get(field_name) is not None:
                any_quantity_provided = True
                break

        if not any_quantity_provided:
            # Only raise error if it's a new stock item and no quantities are provided
            # For existing stock, quantities can be zeroed out
            if not self.initial.get(
                "stock_item_id"
            ):  # Assuming stock_item_id is passed for updates
                self.add_error(
                    None, "At least one branch must have a quantity assigned."
                )

        return cleaned_data

    def save(self):
        name = self.cleaned_data["name"]
        unit_value = self.cleaned_data["unit_value"]

        with transaction.atomic():
            for branch in self.branches:
                field_name = f"quantity_branch_{branch.id}"
                quantity = self.cleaned_data.get(field_name)

                if quantity is not None:
                    stock, created = Stock.objects.update_or_create(
                        name=name,
                        branch=branch,
                        defaults={"quantity": quantity, "unit_value": unit_value},
                    )
        return True  # Indicate success


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
            "bank_paid",
        ]
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "bank_paid": forms.TextInput(attrs={"class": "form-control"}),
            "customer_contact": forms.TextInput(attrs={"class": "form-control"}),
            "amount_paid_cash": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "credit_owed": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }


class SaleRecordUpdateForm(forms.ModelForm):
    class Meta:
        model = SalesRecord
        fields = ["amount_paid_cash", "credit_owed"]
        widgets = {
            "amount_paid_cash": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "credit_owed": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "readonly": "readonly",
                }  # credit_owed will be recalculated
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount_paid_cash = cleaned_data.get("amount_paid_cash")

        # Access the instance to get total_amount
        if self.instance and amount_paid_cash is not None:
            if amount_paid_cash > self.instance.total_amount:
                self.add_error(
                    "amount_paid_cash", "Amount paid cannot exceed total amount."
                )

            # Recalculate credit_owed based on new amount_paid_cash
            cleaned_data["credit_owed"] = self.instance.total_amount - amount_paid_cash

        return cleaned_data


class SalesItemForm(forms.ModelForm):
    class Meta:
        model = SalesItem
        fields = ["stock_item", "quantity_sold", "price_at_sale"]
        widgets = {
            "stock_item": forms.Select(attrs={"class": "form-select"}),
            "quantity_sold": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
            "price_at_sale": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop("branch", None)
        super().__init__(*args, **kwargs)
        if self.branch:
            self.fields["stock_item"].queryset = Stock.objects.filter(
                branch=self.branch
            )
        else:
            self.fields["stock_item"].queryset = Stock.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        stock_item = cleaned_data.get("stock_item")
        quantity_sold = cleaned_data.get("quantity_sold")

        if stock_item and quantity_sold:
            if stock_item.quantity < quantity_sold:
                self.add_error(
                    "quantity_sold",
                    f"Only {stock_item.quantity} of {stock_item.name} available in stock.",
                )
        return cleaned_data


SalesItemFormSet = inlineformset_factory(
    SalesRecord, SalesItem, form=SalesItemForm, extra=1, can_delete=True
)
