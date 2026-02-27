from django import forms
from .models import Vehicle, JobSheet, InternalEstimate, EstimatePart
from accounts.models import CustomUser


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            "image",
            "customer_name",
            "address",
            "phone",
            "job_no",
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
            "job_no": forms.TextInput(attrs={"class": "form-control"}),
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

        # Define formfield_callback to filter queryset for service_advisor
        # This is a more robust way to filter choices statically
        def formfield_for_choice_field(db_field, **kwargs):
            # Extract the widget from kwargs if it exists, as Django's fields_for_model passes it.
            widget = kwargs.pop("widget", None)

            if db_field.name == "service_advisor":
                # For 'service_advisor', we explicitly set our custom widget.
                return forms.ModelChoiceField(
                    queryset=CustomUser.objects.filter(
                        access_level=CustomUser.AccessLevel.WORKSHOP
                    ),
                    widget=forms.Select(attrs={"class": "form-control"}),
                    **kwargs  # Pass remaining kwargs (without the original 'widget')
                )
            # For other fields, pass the extracted widget (if it existed) and other kwargs.
            return db_field.formfield(widget=widget, **kwargs)

        formfield_callback = formfield_for_choice_field


class InternalEstimateForm(forms.ModelForm):
    class Meta:
        model = InternalEstimate
        fields = ["apply_vat", "discount_amount", "is_invoice"]
        # Removed custom widgets to simplify and avoid potential recursion issues
        widgets = {
            "apply_vat": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "discount_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}
            ),
            "is_invoice": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class EstimatePartForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = EstimatePart
        fields = ["id", "name", "price", "quantity"]
        # Removed custom widgets to simplify and avoid potential recursion issues
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
        }
