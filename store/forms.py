from django import forms
from .models import Inventory
from accounts.models import Branch


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
