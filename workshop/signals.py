from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import InternalEstimate, EstimatePart
from decimal import Decimal # Import Decimal

@receiver(post_save, sender=InternalEstimate)
@receiver(post_delete, sender=EstimatePart)
def update_internal_estimate_totals(sender, instance, **kwargs):
    if isinstance(instance, EstimatePart):
        internal_estimate = instance.estimate
    else: # instance is InternalEstimate
        internal_estimate = instance
    
    # Disconnect the signal to prevent recursion
    post_save.disconnect(update_internal_estimate_totals, sender=InternalEstimate)
    post_delete.disconnect(update_internal_estimate_totals, sender=EstimatePart)

    try:
        # Recalculate grand_total
        current_grand_total = internal_estimate.grand_total

        if internal_estimate.apply_vat:
            internal_estimate.vat_amount = current_grand_total * Decimal('0.075') # 7.5% VAT
            internal_estimate.total_with_vat = current_grand_total + internal_estimate.vat_amount
        else:
            internal_estimate.vat_amount = Decimal('0.00')
            internal_estimate.total_with_vat = current_grand_total
        
        # Save if the values have actually changed
        # We don't need to compare with _original_vat_amount here because we've disconnected the signal
        # and this save won't trigger it again.
        internal_estimate.save(update_fields=['vat_amount', 'total_with_vat'])
    finally:
        # Reconnect the signal
        post_save.connect(update_internal_estimate_totals, sender=InternalEstimate)
        post_delete.connect(update_internal_estimate_totals, sender=EstimatePart)
