from django import forms
from .models import Stock, SalesRecord, SalesItem, Branch
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ["name", "quantity", "unit_value", "branch"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "unit_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["branch"].widget.attrs["class"] = "form-select"

        if user and user.access_level != "admin":
            self.fields["branch"].widget = forms.HiddenInput()
        else:
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


class SalesItemForm(forms.ModelForm):
    class Meta:
        model = SalesItem
        fields = ["stock_item", "quantity_sold", "price_at_sale"]
        widgets = {
            "stock_item": forms.Select(attrs={"class": "form-select"}),
            "quantity_sold": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "price_at_sale": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.branch = kwargs.pop("branch", None)
        super().__init__(*args, **kwargs)
        if self.branch:
            self.fields["stock_item"].queryset = Stock.objects.filter(branch=self.branch)
        else:
            self.fields["stock_item"].queryset = Stock.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        stock_item = cleaned_data.get("stock_item")
        quantity_sold = cleaned_data.get("quantity_sold")

        if stock_item and quantity_sold:
            if stock_item.quantity < quantity_sold:
                self.add_error("quantity_sold", f"Only {stock_item.quantity} of {stock_item.name} available in stock.")
        return cleaned_data


SalesItemFormSet = inlineformset_factory(
    SalesRecord, SalesItem, form=SalesItemForm, extra=1, can_delete=True
)
