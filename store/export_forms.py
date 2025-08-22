from django import forms
from .models import Inventory, SalesRecord, SalesItem

class InventoryExportForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inventory_fields = [(field.name, field.verbose_name) for field in Inventory._meta.fields]
        self.fields['fields_to_export'] = forms.MultipleChoiceField(
            choices=inventory_fields,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            initial=[field.name for field in Inventory._meta.fields]
        )

class SalesExportForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Include fields from SalesRecord and related SalesItem (VIN)
        sales_record_fields = [(field.name, field.verbose_name) for field in SalesRecord._meta.fields]
        
        # Add a custom field for Inventory Item VIN from SalesItem
        # This assumes SalesRecord has a reverse relation to SalesItem (salesitem_set)
        # and SalesItem has a foreign key to Inventory (inventory_item)
        custom_fields = [('inventory_item_vin', 'Inventory Item VIN')]
        
        all_fields = sales_record_fields + custom_fields

        self.fields['fields_to_export'] = forms.MultipleChoiceField(
            choices=all_fields,
            widget=forms.CheckboxSelectMultiple,
            required=False,
            initial=[field[0] for field in all_fields]
        )
