from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Inventory, SalesRecord, SalesItem
from .forms import InventoryForm, SalesRecordForm, SalesItemFormSet
from .export_forms import InventoryExportForm, SalesExportForm
from accounts.models import Branch
from django.db.models import Q, Sum
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from django.views import View


@login_required
def add_inventory(request):
    # Only allow admin, sales, and manager users
    if request.user.access_level not in ["admin", "manager"]:
        messages.error(request, "You do not have permission to add inventory.")
        return redirect("store:inventory_list")

    if request.method == "POST":
        form = InventoryForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            inventory = form.save(commit=False)

            # For non-admins, assign branch automatically
            if request.user.access_level != "admin":
                inventory.branch = request.user.branch

            inventory.save()
            messages.success(request, "Inventory added successfully.")
            return redirect("store:inventory_list")
    else:
        form = InventoryForm(user=request.user)

    return render(request, "store/add_inventory.html", {"form": form})


@login_required
def inventory_detail(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk)

    if request.method == "POST":
        # Only allow admin and manager users to update inventory
        if request.user.access_level not in ["admin", "manager"]:
            messages.error(request, "You do not have permission to update inventory.")
            return redirect("store:inventory_detail", pk=inventory.pk)

        form = InventoryForm(
            request.POST, request.FILES, instance=inventory, user=request.user
        )
        if form.is_valid():
            inventory = form.save(commit=False)

            # Prevent branch change if not admin
            if request.user.access_level != "admin":
                inventory.branch = request.user.branch

            inventory.save()
            messages.success(request, "Inventory updated successfully.")
            return redirect("store:inventory_detail", pk=inventory.pk)
    else:
        form = InventoryForm(instance=inventory, user=request.user)

    return render(
        request, "store/inventory_detail.html", {"form": form, "inventory": inventory}
    )


@login_required
def inventory_list(request):
    inventories = Inventory.objects.all()
    branch_filter = request.GET.get("branch")
    query = request.GET.get("q")

    # Apply branch filter if specified
    if branch_filter:
        inventories = inventories.filter(branch_id=branch_filter)

    if query:
        inventories = inventories.filter(
            Q(make__icontains=query)
            | Q(model__icontains=query)
            | Q(vin__icontains=query)
        )

    # Show all branches to everyone for filtering purposes
    branches = Branch.objects.all()

    context = {
        "inventories": inventories,
        "branches": branches,
        "selected_branch": branch_filter,
    }
    return render(request, "store/inventory_list.html", context)


@login_required
def sales_dashboard(request):
    from_date_str = request.GET.get("from_date")
    to_date_str = request.GET.get("to_date")

    sales_records_queryset = SalesRecord.objects.all()

    if from_date_str:
        try:
            from_date = timezone.make_aware(
                datetime.strptime(from_date_str, "%Y-%m-%d")
            )
            sales_records_queryset = sales_records_queryset.filter(
                sale_date__gte=from_date
            )
        except ValueError:
            messages.error(
                request, "Invalid 'from date' format. Please use YYYY-MM-DD."
            )

    if to_date_str:
        try:
            to_date = (
                timezone.make_aware(datetime.strptime(to_date_str, "%Y-%m-%d"))
                + timedelta(days=1)
                - timedelta(microseconds=1)
            )
            sales_records_queryset = sales_records_queryset.filter(
                sale_date__lte=to_date
            )
        except ValueError:
            messages.error(request, "Invalid 'to date' format. Please use YYYY-MM-DD.")

    if request.user.access_level in ["admin", "manager"]:
        # Admin and Manager see an overview of all branches
        branches = Branch.objects.all()
        branch_sales_summary = []

        for branch in branches:
            branch_sales_qs = sales_records_queryset.filter(branch=branch)
            total_sales_records = branch_sales_qs.count()
            total_cash_sales = (
                branch_sales_qs.aggregate(Sum("amount_paid_cash"))[
                    "amount_paid_cash__sum"
                ]
                or 0
            )
            total_credit_sales = (
                branch_sales_qs.aggregate(Sum("credit_owed"))["credit_owed__sum"] or 0
            )
            total_overall_sales = (
                branch_sales_qs.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
            )

            branch_sales_summary.append(
                {
                    "branch": branch,
                    "total_sales_records": total_sales_records,
                    "total_cash_sales": total_cash_sales,
                    "total_credit_sales": total_credit_sales,
                    "total_overall_sales": total_overall_sales,
                }
            )
        context = {
            "branch_sales_summary": branch_sales_summary,
            "is_admin_or_manager": True,
            "from_date": from_date_str,
            "to_date": to_date_str,
        }
        return render(request, "store/sales_overview.html", context)
    else:
        # Other staff see only their branch's sales records
        user_branch = request.user.branch
        if not user_branch:
            messages.error(request, "You are not assigned to any branch.")
            return redirect("home:dashboard")  # Redirect to a safe page

        sales_records = SalesRecord.objects.filter(branch=user_branch).order_by(
            "-sale_date"
        )
        context = {
            "sales_records": sales_records,
            "branch_name": user_branch.name,
            "is_admin_or_manager": False,
            "can_create_sales": request.user.access_level
            == "sales",  # Assuming 'sales' is the access_level for sales staff
        }
        return render(request, "store/sales_detail.html", context)


@login_required
def sales_detail_branch(request, branch_pk):
    branch = get_object_or_404(Branch, pk=branch_pk)

    # Ensure only admin/manager can access this detailed view directly
    if request.user.access_level not in ["admin", "manager"]:
        messages.error(
            request, "You do not have permission to view other branch's sales details."
        )
        return redirect("store:sales_dashboard")

    sales_records = SalesRecord.objects.filter(branch=branch).order_by("-sale_date")
    context = {
        "sales_records": sales_records,
        "branch_name": branch.name,
        "is_admin_or_manager": True,
    }
    return render(request, "store/sales_detail.html", context)


@login_required
def create_sales_record(request):
    # Only sales staff can create sales records
    if request.user.access_level != "sales":
        messages.error(request, "You do not have permission to create sales records.")
        return redirect("store:sales_dashboard")

    if request.method == "POST":
        form = SalesRecordForm(request.POST)  # Removed request=request
        formset = SalesItemFormSet(
            request.POST, instance=SalesRecord()
        )  # Pass an empty instance for initial formset
        if form.is_valid() and formset.is_valid():
            sales_record = form.save(commit=False)
            sales_record.branch = request.user.branch  # Assign branch automatically
            # Marketer is now a CharField, so it's saved directly by the form
            sales_record.save()

            total_amount = 0
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get("DELETE"):
                    vin = item_form.cleaned_data.get("vin")
                    quantity = item_form.cleaned_data.get("quantity")
                    price_at_sale = item_form.cleaned_data.get("price_at_sale")

                    try:
                        inventory_item = Inventory.objects.get(vin=vin)
                        if inventory_item.status == "sold":
                            messages.error(
                                request,
                                f"Vehicle with VIN {vin} is already sold and cannot be re-sold.",
                            )
                            return render(
                                request,
                                "store/create_sales_record.html",
                                {"form": form, "formset": formset},
                            )

                        sales_item = SalesItem.objects.create(
                            sales_record=sales_record,
                            inventory_item=inventory_item,
                            price_at_sale=price_at_sale,
                        )
                        total_amount += sales_item.price_at_sale

                        # Update inventory status to "sold"
                        inventory_item.status = "sold"
                        inventory_item.save()  # This will trigger the custom save method in Inventory model
                    except Inventory.DoesNotExist:
                        messages.error(
                            request, f"No inventory item found with VIN: {vin}."
                        )
                        return render(
                            request,
                            "store/create_sales_record.html",
                            {"form": form, "formset": formset},
                        )
                    except ValueError as e:
                        messages.error(
                            request,
                            f"Error updating inventory status for VIN {vin}: {e}",
                        )
                        return render(
                            request,
                            "store/create_sales_record.html",
                            {"form": form, "formset": formset},
                        )

            sales_record.total_amount = total_amount
            sales_record.save()

            messages.success(request, "Sales record created successfully.")
            return redirect("store:sales_dashboard")
    else:
        form = SalesRecordForm()  # Removed request=request
        formset = SalesItemFormSet(instance=SalesRecord())

    context = {
        "form": form,
        "formset": formset,
    }
    return render(request, "store/create_sales_record.html", context)


class InventoryExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True # Raise 403 if test_func returns False

    def test_func(self):
        return self.request.user.access_level in ["admin", "manager"]

    def get(self, request):
        form = InventoryExportForm(request.GET)
        inventories = Inventory.objects.all()

        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            fields_to_export = form.cleaned_data.get('fields_to_export')

            if start_date:
                inventories = inventories.filter(added_on__gte=start_date)
            if end_date:
                inventories = inventories.filter(added_on__lte=end_date)

            if 'export' in request.GET:
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="inventory_export.xlsx"'

                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = "Inventory"

                # Apply styles
                header_font = Font(bold=True)
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                center_aligned_text = Alignment(horizontal="center")

                # Write headers
                headers = [Inventory._meta.get_field(field_name).verbose_name for field_name in fields_to_export]
                worksheet.append(headers)
                for col in range(1, len(headers) + 1):
                    worksheet.cell(row=1, column=col).font = header_font
                    worksheet.cell(row=1, column=col).border = thin_border
                    worksheet.cell(row=1, column=col).alignment = center_aligned_text

                # Write data
                for item in inventories:
                    row_data = []
                    for field_name in fields_to_export:
                        value = getattr(item, field_name)
                        # Convert non-primitive Django model objects to their string representation
                        if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, datetime)):
                            row_data.append(str(value))
                        elif isinstance(value, datetime) and timezone.is_aware(value):
                            row_data.append(timezone.make_naive(value)) # Convert to naive datetime
                        else:
                            row_data.append(value)
                    worksheet.append(row_data)
                    for col in range(1, len(row_data) + 1):
                        worksheet.cell(row=worksheet.max_row, column=col).border = thin_border

                workbook.save(response)
                return response
        
        # Prepare headers for template preview
        template_headers = []
        if form.is_valid() and fields_to_export:
            for field_name in fields_to_export:
                template_headers.append(Inventory._meta.get_field(field_name).verbose_name)

        context = {
            'form': form,
            'inventories': inventories,
            'template_headers': template_headers,
        }
        return render(request, 'store/inventory_export.html', context)


class SalesExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    raise_exception = True # Raise 403 if test_func returns False

    def test_func(self):
        return self.request.user.access_level in ["admin", "manager"]

    def get(self, request):
        form = SalesExportForm(request.GET)
        sales_records = SalesRecord.objects.all()

        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            fields_to_export = form.cleaned_data.get('fields_to_export')

            if start_date:
                sales_records = sales_records.filter(sale_date__gte=start_date)
            if end_date:
                sales_records = sales_records.filter(sale_date__lte=end_date)

            if 'export' in request.GET:
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="sales_export.xlsx"'

                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = "Sales"

                # Apply styles
                header_font = Font(bold=True)
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                center_aligned_text = Alignment(horizontal="center")

                # Write headers
                headers = []
                for field_name in fields_to_export:
                    if field_name == 'inventory_item_vin': # Custom field for VIN
                        headers.append('Inventory Item VIN')
                    else:
                        headers.append(SalesRecord._meta.get_field(field_name).verbose_name)
                worksheet.append(headers)
                for col in range(1, len(headers) + 1):
                    worksheet.cell(row=1, column=col).font = header_font
                    worksheet.cell(row=1, column=col).border = thin_border
                    worksheet.cell(row=1, column=col).alignment = center_aligned_text

                # Write data
                for record in sales_records:
                    row_data = []
                    for field_name in fields_to_export:
                        if field_name == 'inventory_item_vin':
                            sales_items = SalesItem.objects.filter(sales_record=record)
                            vins = ", ".join([item.inventory_item.vin for item in sales_items])
                            row_data.append(vins)
                        else:
                            value = getattr(record, field_name)
                            # Convert non-primitive Django model objects to their string representation
                            if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, datetime)):
                                row_data.append(str(value))
                            elif isinstance(value, datetime) and timezone.is_aware(value):
                                row_data.append(timezone.make_naive(value)) # Convert to naive datetime
                            else:
                                row_data.append(value)
                    worksheet.append(row_data)
                    for col in range(1, len(row_data) + 1):
                        worksheet.cell(row=worksheet.max_row, column=col).border = thin_border

                workbook.save(response)
                return response

        # Prepare headers for template preview
        template_headers = []
        if form.is_valid() and fields_to_export:
            for field_name in fields_to_export:
                if field_name == 'inventory_item_vin':
                    template_headers.append('Inventory Item VIN')
                else:
                    template_headers.append(SalesRecord._meta.get_field(field_name).verbose_name)

        context = {
            'form': form,
            'sales_records': sales_records,
            'template_headers': template_headers,
        }
        return render(request, 'store/sales_export.html', context)
