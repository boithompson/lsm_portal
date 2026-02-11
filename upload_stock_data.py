import os
import django
import pandas as pd
from decimal import Decimal

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lsm_portal.settings")
django.setup()

from store.models import Stock
from accounts.models import Branch


def upload_stock_data(excel_file_path):
    df = pd.read_excel(excel_file_path, sheet_name="CURRENT STOCK", header=None)

    # Identify the header row (row 2 in the excel, index 1 in pandas)
    header_row_index = 1
    headers = df.iloc[header_row_index].tolist()

    # Extract branch names from the header
    branch_names = headers[1:12]  # ALAKA to CITI CARS

    # Data starts from row 4 (index 3)
    for r_idx in range(3, len(df)):
        row_data = df.iloc[r_idx].tolist()
        product_name = str(row_data[0]).strip()

        if (
            not product_name
            or product_name.startswith("TOTAL")
            or product_name.startswith("STOCK AS AT")
            or product_name.startswith("PRODUCTS")
        ):
            continue  # Skip empty rows, total rows, and header-like rows

        unit_value_raw = row_data[13]  # UNIT VALUE column
        unit_value = Decimal("0.00")  # Default to 0.00

        if (
            pd.notna(unit_value_raw)
            and str(unit_value_raw).strip() != ""
            and str(unit_value_raw).strip() != "[object Object]"
        ):
            try:
                unit_value = Decimal(str(unit_value_raw).replace(",", ""))
            except (ValueError, TypeError):
                print(
                    f"Could not parse unit value for product {product_name}: {unit_value_raw}. Defaulting to 0.00"
                )
                unit_value = Decimal("0.00")
        else:
            print(
                f"Invalid or missing unit value for product {product_name}: {unit_value_raw}. Defaulting to 0.00"
            )

        for i, branch_name in enumerate(branch_names):
            if not branch_name or pd.isna(branch_name):
                continue

            quantity_str = row_data[
                i + 1
            ]  # Quantity for each branch starts from column B (index 1)
            try:
                quantity = (
                    int(quantity_str)
                    if pd.notna(quantity_str) and str(quantity_str).strip() != ""
                    else 0
                )
            except (ValueError, TypeError):
                quantity = 0  # Default to 0 if quantity is not a valid number

            if quantity == 0:
                print(f"Skipping {product_name} at {branch_name} due to zero quantity.")
                continue  # Skip if quantity is zero

            # Get or create Branch
            branch, created = Branch.objects.get_or_create(name=branch_name)
            if created:
                print(f"Created new branch: {branch_name}")

            # Get or update Stock
            stock_item, created = Stock.objects.get_or_create(
                branch=branch,
                name=product_name,
                defaults={"quantity": quantity, "unit_value": unit_value},
            )

            if not created:
                # If stock item exists, update quantity and unit_value
                stock_item.quantity += quantity  # Add to existing quantity
                stock_item.unit_value = unit_value  # Update unit value
                stock_item.save()
                print(
                    f"Updated stock for {product_name} at {branch_name}. New quantity: {stock_item.quantity}"
                )
            else:
                print(
                    f"Created new stock item: {product_name} at {branch_name} with quantity {quantity}"
                )


if __name__ == "__main__":
    excel_file_name = "stock.xlsx"
    excel_file_path = os.path.join(os.getcwd(), excel_file_name)
    upload_stock_data(excel_file_path)
    print("Stock data upload complete.")
