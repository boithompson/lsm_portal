from django import forms
from .models import Vehicle, JobSheet, InternalEstimate, EstimatePart


class WorkshopExportForm(forms.Form):
    start_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vehicle_fields = [
            (field.name, field.verbose_name.title()) for field in Vehicle._meta.fields
        ]

        # Add custom fields for Job Sheet and Estimate information
        custom_fields = [
            ("job_sheet_service_advisor", "Service Advisor"),
            ("job_sheet_assigned_to", "Assigned To"),
            ("job_sheet_accessories", "Accessories"),
            ("job_sheet_job_description", "Job Description"),
            ("estimate_apply_vat", "Apply VAT"),
            ("estimate_discount_amount", "Discount Amount"),
            ("estimate_is_invoice", "Is Invoice"),
            ("estimate_grand_total", "Grand Total"),
            ("estimate_parts_details", "Parts Details"),
        ]

        all_fields = vehicle_fields + custom_fields

        self.fields["fields_to_export"] = forms.MultipleChoiceField(
            choices=all_fields,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            initial=[field[0] for field in all_fields],
        )
