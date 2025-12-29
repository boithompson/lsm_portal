from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Vehicle, InternalEstimate, EstimatePart
import datetime # Import datetime
from functools import wraps
from django.contrib import messages

def workshop_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login") # Redirect to login if not authenticated
        if request.user.access_level not in ["admin", "workshop", "procurement"]:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("home:dashboard")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@workshop_access_required
def print_proforma_invoice(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    internal_estimate = get_object_or_404(InternalEstimate, vehicle=vehicle)
    estimate_parts = internal_estimate.estimatepart_set.all()

    # The apply_vat field should be set when the InternalEstimate is created/edited.
    # We will just use the value stored in the database.
    # Ensure the save method is called to update VAT if parts have changed
    internal_estimate.save()

    # Calculate subtotal
    subtotal = sum(part.price * part.quantity for part in estimate_parts)

    context = {
        "vehicle": vehicle,
        "internal_estimate": internal_estimate,
        "estimate_parts": estimate_parts,
        "subtotal": subtotal,
        "date_now": datetime.date.today(), # Add current date to context
        "vat_applied": internal_estimate.apply_vat,
        "is_invoice": internal_estimate.is_invoice, # Pass invoice status to template
    }
    return render(request, "workshop/proforma_invoice.html", context)
