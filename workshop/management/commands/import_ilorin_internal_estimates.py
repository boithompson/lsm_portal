import pandas as pd
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from lsm_portal import settings
from workshop.models import Vehicle, InternalEstimate, EstimatePart
from accounts.models import Branch
from datetime import datetime
import os


def safe_decimal(value):
    """
    Safely convert Excel value to Decimal.
    Handles commas, currency symbols, empty strings and NaN.
    """
    try:
        if pd.isna(value):
            return Decimal("0.00")

        cleaned = (
            str(value)
            .replace(",", "")
            .replace("₦", "")
            .strip()
        )

        if cleaned == "":
            return Decimal("0.00")

        return Decimal(cleaned)

    except (InvalidOperation, ValueError):
        return Decimal("0.00")


class Command(BaseCommand):
    help = "Import ILORIN Internal Estimates from Excel"

    def handle(self, *args, **kwargs):

        file_path = os.path.join(
            settings.BASE_DIR,
            "data",
            "ILORIN_BRANCH_JAN_2026.xlsx"
        )

        sheet_name = "INTERNAL ESTIMATES"

        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

        # Safer branch retrieval
        branch, _ = Branch.objects.get_or_create(name="ILORIN")

        i = 0
        while i < len(df):

            row = df.iloc[i]

            # Detect start of a new estimate block
            if isinstance(row[0], str) and "Customer :" in row[0]:

                customer_name = row[1]

                vehicle_brand = df.iloc[i + 2][1]
                model = df.iloc[i + 2][4]
                year = df.iloc[i + 2][9]

                registration = df.iloc[i + 4][1]
                mileage = df.iloc[i + 4][5]
                vin = df.iloc[i + 4][9]

                estimate_date_raw = df.iloc[i - 1][9]
                try:
                    estimate_date = datetime.strptime(
                        str(estimate_date_raw), "%d/%m/%Y"
                    ).date()
                except Exception:
                    estimate_date = datetime.today().date()

                # -------------------------
                # CREATE VEHICLE
                # -------------------------
                vehicle = Vehicle.objects.create(
                    branch=branch,
                    customer_name=str(customer_name),
                    address="",
                    phone="",
                    vehicle_make=str(vehicle_brand),
                    model=str(model),
                    year=int(year) if not pd.isna(year) else 2000,
                    chasis_no=str(vin),
                    licence_plate=str(registration),
                    date_of_first_registration=estimate_date,
                    mileage=str(mileage),
                    complaint="Imported from Excel",
                )

                # -------------------------
                # CREATE ESTIMATE
                # -------------------------
                estimate = InternalEstimate.objects.create(
                    vehicle=vehicle
                )

                # -------------------------
                # PARTS SECTION
                # -------------------------
                j = i
                while j < len(df):

                    if (
                        isinstance(df.iloc[j][2], str)
                        and df.iloc[j][2].strip().upper() == "SUBTOTAL"
                    ):
                        break

                    description = df.iloc[j][2]
                    qty = df.iloc[j][5]
                    internal_value = df.iloc[j][6]

                    if (
                        isinstance(description, str)
                        and description.strip().upper()
                        not in ["S. NO.", "DESCRIPTION", ""]
                        and not pd.isna(qty)
                    ):
                        quantity = int(qty) if not pd.isna(qty) else 1
                        price = safe_decimal(internal_value)

                        EstimatePart.objects.create(
                            estimate=estimate,
                            name=description.strip(),
                            quantity=quantity,
                            price=price,
                        )

                    j += 1

                # -------------------------
                # VAT + DISCOUNT
                # -------------------------
                vat_amount = Decimal("0.00")
                discount_amount = Decimal("0.00")

                for k in range(j, j + 10):
                    if k >= len(df):
                        break

                    label = df.iloc[k][2]

                    if isinstance(label, str):
                        label_upper = label.strip().upper()

                        if label_upper == "VAT":
                            vat_amount = safe_decimal(df.iloc[k][9])

                        if label_upper == "DISCOUNT":
                            discount_amount = safe_decimal(df.iloc[k][9])

                estimate.vat_amount = vat_amount
                estimate.discount_amount = discount_amount
                estimate.apply_vat = vat_amount > 0
                estimate.total_with_vat = estimate.grand_total
                estimate.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Imported vehicle {vehicle.licence_plate}"
                    )
                )

                i = j

            i += 1

        self.stdout.write(
            self.style.SUCCESS("Import completed successfully.")
        )