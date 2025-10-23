from django import forms
from .models import Vehicle, JobSheet, InternalEstimate, EstimatePart


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "image",
            "customer_name",
            "address",
            "phone",
            "vehicle_make",
            "model",
            "year",
            "chasis_no",
            "licence_plate",
            "date_of_first_registration",
            "mileage",
            "complaint",
        ]
        widgets = {
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "vehicle_make": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "chasis_no": forms.TextInput(attrs={"class": "form-control"}),
            "licence_plate": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_first_registration": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "mileage": forms.TextInput(attrs={"class": "form-control"}),
            "complaint": forms.Textarea(attrs={"class": "form-control"}),
        }


class JobSheetForm(forms.ModelForm):
    assigned_to = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}), required=False
    )

    class Meta:
        model = JobSheet
        fields = ["service_advisor", "assigned_to", "accessories", "job_description"]
        widgets = {
            "service_advisor": forms.Select(attrs={"class": "form-control"}),
            "accessories": forms.Textarea(attrs={"class": "form-control"}),
            "job_description": forms.Textarea(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service_advisor"].queryset = self.fields[
            "service_advisor"
        ].queryset.filter(access_level="workshop")


class InternalEstimateForm(forms.ModelForm):
    class Meta:
        model = InternalEstimate
        fields = ['apply_vat', 'is_invoice']
        widgets = {
            'apply_vat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_invoice': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EstimatePartForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = EstimatePart
        fields = ["id", "name", "price", "quantity"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
        }
