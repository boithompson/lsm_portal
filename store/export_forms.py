from django import forms
from .models import Stock, SalesRecord, SalesItem


class StockExportForm(forms.Form):
    start_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stock_fields = [
            (field.name, field.verbose_name) for field in Stock._meta.fields
        ]
        self.fields["fields_to_export"] = forms.MultipleChoiceField(
            choices=stock_fields,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            initial=[field.name for field in Stock._meta.fields],
        )


class SalesExportForm(forms.Form):
    start_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sales_record_fields = [
            (field.name, field.verbose_name) for field in SalesRecord._meta.fields
        ]

        # Add custom fields for Stock Item Name and Quantity Sold from SalesItem
        custom_fields = [
            ("stock_item_name", "Stock Item Name"),
            ("quantity_sold", "Quantity Sold"),
        ]

        all_fields = sales_record_fields + custom_fields

        self.fields["fields_to_export"] = forms.MultipleChoiceField(
            choices=all_fields,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            initial=[field[0] for field in all_fields],
        )
