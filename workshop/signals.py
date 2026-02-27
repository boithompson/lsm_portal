from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import InternalEstimate, EstimatePart
from decimal import Decimal  # Import Decimal


@receiver(post_save, sender=InternalEstimate)
@receiver(post_delete, sender=EstimatePart)
def update_internal_estimate_totals(sender, instance, **kwargs):
    # Avoid recursion if this save is already triggered by the signal itself
    if kwargs.get("raw"):  # raw=True for initial data loading, don't run signals
        return

    if isinstance(instance, EstimatePart):
        internal_estimate = instance.estimate
    else:  # instance is InternalEstimate
        internal_estimate = instance

    # Ensure internal_estimate still exists before proceeding
    # This check is crucial for post_delete of EstimatePart, where InternalEstimate might be gone
    if not InternalEstimate.objects.filter(pk=internal_estimate.pk).exists():
        return

    # Recalculate grand_total
    current_grand_total = internal_estimate.grand_total

    # Calculate new VAT and total amounts
    new_vat_amount = Decimal("0.00")
    new_total_with_vat = current_grand_total

    if internal_estimate.apply_vat:
        new_vat_amount = Decimal(str(current_grand_total)) * Decimal(
            "0.075"
        )  # 7.5% VAT
        new_total_with_vat = Decimal(str(current_grand_total)) + new_vat_amount

    # Only save if the calculated values are different from the current values on the instance
    if (internal_estimate.vat_amount != new_vat_amount) or (
        internal_estimate.total_with_vat != new_total_with_vat
    ):

        internal_estimate.vat_amount = new_vat_amount
        internal_estimate.total_with_vat = new_total_with_vat
        # Use update_fields to prevent re-triggering post_save for the entire instance
        internal_estimate.save(update_fields=["vat_amount", "total_with_vat"])
