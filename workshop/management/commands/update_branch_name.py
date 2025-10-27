from django.core.management.base import BaseCommand
from workshop.models import Vehicle, Branch

class Command(BaseCommand):
    help = "Update all vehicles with branch name 'Abuja' to 'ABUJA'"

    def handle(self, *args, **options):
        # Fetch or create the uppercase branch
        abuja_branch, _ = Branch.objects.get_or_create(name="ABUJA")

        # Get all vehicles currently assigned to 'Abuja' (case-insensitive)
        vehicles_to_update = Vehicle.objects.filter(branch__name__iexact="Abuja")

        total = vehicles_to_update.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No vehicles found with branch name 'Abuja'."))
            return

        self.stdout.write(self.style.WARNING(f"Found {total} vehicles — updating..."))

        # Update each vehicle’s branch to 'ABUJA'
        for vehicle in vehicles_to_update:
            vehicle.branch = abuja_branch
            vehicle.save(update_fields=["branch"])

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully updated {total} vehicles to branch 'ABUJA'."))
