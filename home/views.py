from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.forms import inlineformset_factory
from accounts.models import CustomUser, Branch
from workshop.models import (
    Vehicle,
    JobSheet,
    InternalEstimate,
    EstimatePart,
    VehicleStatus,
)
from store.models import Stock  # Import Stock model
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from workshop.forms import (
    VehicleForm,
    JobSheetForm,
    InternalEstimateForm,
    EstimatePartForm,
)
from django.core.paginator import Paginator
import datetime


@login_required
def dashboard(request):
    branches = Branch.objects.all()
    branch_inventory_data = []

    for branch in branches:
        total_stock_items = Stock.objects.filter(branch=branch).count()
        branch_inventory_data.append(
            {
                "branch_name": branch.name,
                "total_stock_items": total_stock_items,
                "branch_id": branch.id,
            }
        )

    context = {
        "branch_inventory_data": branch_inventory_data,
    }
    return render(request, "home/dashboard.html", context)


@login_required
def staffs(request):
    if request.user.access_level not in ["admin", "manager"]:
        return redirect("home:dashboard")

    if request.user.access_level == "admin":
        users = CustomUser.objects.exclude(access_level="admin")
    else:  # Manager
        users = CustomUser.objects.filter(branch=request.user.branch).exclude(
            access_level="admin"
        )

    context = {"staffs": users}
    return render(request, "home/staffs.html", context)


from django.contrib.auth.mixins import AccessMixin
from functools import wraps


def workshop_access_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            if not request.user.is_authenticated:
                return redirect(
                    "accounts:login"
                )  # Redirect to login if not authenticated
            if request.user.access_level not in [
                "admin",
                "workshop",
                "procurement",
                "account",
            ]:
                messages.error(
                    request, "You do not have permission to access this page."
                )
                return redirect("home:dashboard")
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.exception("Error in workshop_access_required decorator:")
            messages.error(
                request, f"An unexpected error occurred in access check: {e}"
            )
            return redirect("home:dashboard")  # Redirect to a safe page

    return _wrapped_view


import logging

logger = logging.getLogger(__name__)


@login_required
@workshop_access_required
def workshop(request):
    try:
        query = request.GET.get("q")
        status = request.GET.get("status")
        selected_branch_id = request.GET.get("branch")  # for admin filtering

        if request.user.access_level == "admin":
            vehicles = (
                Vehicle.objects.filter(is_master_record=True)
                .annotate(latest_service_date=Max("duplicate_vehicles__date_created"))
                .order_by("-latest_service_date", "-id")
            )
            branches = Branch.objects.all()  # for filter dropdown

            if selected_branch_id:
                vehicles = vehicles.filter(branch__id=selected_branch_id)
        else:
            if request.user.branch:
                vehicles = (
                    Vehicle.objects.filter(
                        branch=request.user.branch, is_master_record=True
                    )
                    .annotate(
                        latest_service_date=Max("duplicate_vehicles__date_created")
                    )
                    .order_by("-latest_service_date", "-id")
                )
            else:
                # If a non-admin user has no branch assigned, they shouldn't see any vehicles
                vehicles = Vehicle.objects.none()
            branches = (
                []
            )  # no need to show branches to non-admins, but provide an empty list

        if query:
            vehicles = vehicles.filter(
                Q(customer_name__icontains=query)
                | Q(vehicle_make__icontains=query)
                | Q(model__icontains=query)
                | Q(licence_plate__icontains=query)
                | Q(chasis_no__icontains=query)
            )

        if status:
            vehicles = vehicles.filter(status=status)

        from django.core.paginator import Paginator

        paginator = Paginator(vehicles, 50)  # Show 50 vehicles per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "page_obj": page_obj,
            "vehicle_status_choices": VehicleStatus.choices,
            "branches": branches,  # will be used for filter dropdown in template
            "selected_branch_id": selected_branch_id,
        }
        return render(request, "home/workshop.html", context)
    except Exception as e:
        logger.exception("Error in workshop view:")
        messages.error(request, f"An unexpected error occurred: {e}")
        return redirect("home:dashboard")  # Redirect to a safe page


@login_required
@workshop_access_required
def find_vehicle_by_chasis(request):
    """Chasis number lookup view for finding existing vehicles"""
    if request.method == "POST":
        chasis_no = request.POST.get("chasis_no", "").strip()
        if chasis_no:
            # Case-insensitive chasis number lookup - only search master records
            master_vehicles = Vehicle.objects.filter(
                chasis_no__iexact=chasis_no, is_master_record=True
            )
            if master_vehicles.exists():
                # Show service history for this chasis number
                master_vehicle = master_vehicles.first()
                # Get all service records (including master and duplicates) for this chasis
                all_vehicles = Vehicle.objects.filter(chasis_no__iexact=chasis_no).order_by("-date_created")
                service_records = all_vehicles.filter(is_master_record=False)

                # Paginate service records
                paginator = Paginator(
                    service_records, 10
                )  # Show 10 service records per page
                page_number = request.GET.get("page")
                page_obj = paginator.get_page(page_number)

                # Calculate total visits including master vehicle
                total_visits = all_vehicles.count()

                context = {
                    "chasis_no": chasis_no,
                    "master_vehicle": master_vehicle,
                    "service_records": page_obj,
                    "total_visits": total_visits,
                    "record_status_choices": VehicleStatus.choices,
                }
                return render(request, "home/vehicle_chasis_lookup.html", context)
            else:
                messages.info(request, f"No vehicle found with Chasis No: {chasis_no}")
        else:
            messages.error(request, "Please enter a Chasis Number")

    # Handle GET request with chasis_no parameter (from vehicle detail page)
    chasis_no = request.GET.get("chasis_no", "").strip()
    if chasis_no:
        # Only search master records first
        master_vehicles = Vehicle.objects.filter(
            chasis_no__iexact=chasis_no, is_master_record=True
        )
        if master_vehicles.exists():
            master_vehicle = master_vehicles.first()
            # Get all service records (including master and duplicates) for this chasis
            all_vehicles = Vehicle.objects.filter(chasis_no__iexact=chasis_no).order_by("-date_created")
            service_records = all_vehicles.filter(is_master_record=False)

            # Paginate service records
            paginator = Paginator(
                service_records, 10
            )  # Show 10 service records per page
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            context = {
                "chasis_no": chasis_no,
                "master_vehicle": master_vehicle,
                "service_records": page_obj,
                "total_visits": all_vehicles.count(),
                "record_status_choices": VehicleStatus.choices,
            }
            return render(request, "home/vehicle_chasis_lookup.html", context)
        else:
            messages.info(request, f"No vehicle found with Chasis No: {chasis_no}")

    return render(request, "home/chasis_lookup.html")


@login_required
@workshop_access_required
def vehicle_detail(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    internal_estimate = InternalEstimate.objects.filter(vehicle=vehicle).first()
    context = {
        "vehicle": vehicle,
        "is_invoice": internal_estimate.is_invoice if internal_estimate else False,
    }
    return render(request, "home/vehicle_detail.html", context)


@login_required
@workshop_access_required
def add_vehicle(request):
    if request.method == "POST":
        form = VehicleForm(request.POST, request.FILES)
        if request.user.access_level == "admin":
            form.fields["branch"] = forms.ModelChoiceField(
                queryset=Branch.objects.all(),
                widget=forms.Select(attrs={"class": "form-control"}),
            )

        if form.is_valid():
            chasis_no = form.cleaned_data.get("chasis_no")
            master_id = request.GET.get("master_id")

            if chasis_no and master_id:
                # Creating a new job for an existing vehicle
                try:
                    master_vehicle = Vehicle.objects.get(
                        id=master_id, chasis_no__iexact=chasis_no
                    )
                    vehicle = form.save(commit=False)
                    vehicle.master_vehicle = master_vehicle
                    vehicle.is_master_record = False
                    vehicle.branch = master_vehicle.branch

                    # Auto-generate job number
                    import datetime

                    today = datetime.date.today()
                    year = today.year
                    month = today.month
                    day = today.day

                    # Get the next job number for this vehicle
                    existing_jobs = Vehicle.objects.filter(
                        master_vehicle=master_vehicle, is_master_record=False
                    ).count()
                    job_number = f"{master_vehicle.uuid}-{year:04d}-{month:02d}-{day:02d}-{existing_jobs + 1:03d}"
                    vehicle.job_no = job_number

                except Vehicle.DoesNotExist:
                    # Fallback to regular logic if master vehicle not found
                    existing_vehicles = Vehicle.objects.filter(
                        chasis_no__iexact=chasis_no
                    )
                    if existing_vehicles.exists():
                        master_vehicle = existing_vehicles.first()
                        vehicle = form.save(commit=False)
                        vehicle.master_vehicle = master_vehicle
                        vehicle.is_master_record = False
                        vehicle.branch = master_vehicle.branch
                    else:
                        vehicle = form.save(commit=False)
                        vehicle.is_master_record = True
                        if request.user.access_level == "admin":
                            vehicle.branch = form.cleaned_data["branch"]
                        else:
                            vehicle.branch = request.user.branch
            elif chasis_no:
                # Check if vehicle with this chasis_no already exists
                existing_vehicles = Vehicle.objects.filter(chasis_no__iexact=chasis_no)
                if existing_vehicles.exists():
                    # Create a new service record linked to the master vehicle
                    master_vehicle = existing_vehicles.first()
                    vehicle = form.save(commit=False)
                    vehicle.master_vehicle = master_vehicle
                    vehicle.is_master_record = False
                    vehicle.branch = (
                        master_vehicle.branch
                    )  # Use master vehicle's branch
                else:
                    # Create new master vehicle record
                    vehicle = form.save(commit=False)
                    vehicle.is_master_record = True
                    if request.user.access_level == "admin":
                        vehicle.branch = form.cleaned_data["branch"]
                    else:
                        vehicle.branch = request.user.branch
            else:
                # No chasis_no provided, create as master record
                vehicle = form.save(commit=False)
                vehicle.is_master_record = True
                if request.user.access_level == "admin":
                    vehicle.branch = form.cleaned_data["branch"]
                else:
                    vehicle.branch = request.user.branch

            vehicle.save()
            messages.success(request, "Vehicle created successfully.")
            return redirect("home:workshop")
    else:
        # Pre-populate form if coming from vehicle detail page
        chasis_no = request.GET.get("chasis_no")
        master_id = request.GET.get("master_id")

        if chasis_no and master_id:
            try:
                master_vehicle = Vehicle.objects.get(
                    id=master_id, chasis_no__iexact=chasis_no
                )
                initial_data = {
                    "customer_name": master_vehicle.customer_name,
                    "address": master_vehicle.address,
                    "phone": master_vehicle.phone,
                    "vehicle_make": master_vehicle.vehicle_make,
                    "model": master_vehicle.model,
                    "year": master_vehicle.year,
                    "chasis_no": master_vehicle.chasis_no,
                    "date_of_first_registration": master_vehicle.date_of_first_registration,
                }
                form = VehicleForm(initial=initial_data)
            except Vehicle.DoesNotExist:
                form = VehicleForm()
        else:
            form = VehicleForm()

        if request.user.access_level == "admin":
            form.fields["branch"] = forms.ModelChoiceField(
                queryset=Branch.objects.all(),
                widget=forms.Select(attrs={"class": "form-control"}),
            )

    context = {
        "form": form,
    }
    return render(request, "home/add_vehicle.html", context)


@login_required
@workshop_access_required
def edit_vehicle(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    if request.method == "POST":
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            return redirect("home:workshop")
    else:
        form = VehicleForm(instance=vehicle)
    context = {
        "form": form,
    }
    return render(request, "home/edit_vehicle.html", context)


@login_required
@workshop_access_required
def update_vehicle_status(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    if request.method == "POST":
        status = request.POST.get("status")
        if status in [choice[0] for choice in VehicleStatus.choices]:
            vehicle.status = status
            vehicle.save()
    return redirect("home:workshop")


@login_required
@workshop_access_required
def delete_vehicle(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    if request.user.access_level in [
        "admin",
        "manager",
    ]:
        vehicle.delete()
        messages.success(request, "Vehicle record deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete vehicle records.")
    return redirect("home:workshop")


@login_required
@workshop_access_required
def create_job_sheet(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    if request.method == "POST":
        form = JobSheetForm(request.POST)
        if form.is_valid():
            job_sheet = form.save(commit=False)
            job_sheet.vehicle = vehicle
            job_sheet.save()
            return redirect("home:vehicle_detail", vehicle_id=vehicle.id)
    else:
        form = JobSheetForm()
    context = {
        "form": form,
        "vehicle": vehicle,
    }
    return render(request, "home/create_job_sheet.html", context)


@login_required
@workshop_access_required
def edit_job_sheet(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    job_sheet = JobSheet.objects.get(vehicle=vehicle)
    if request.method == "POST":
        form = JobSheetForm(request.POST, instance=job_sheet)
        if form.is_valid():
            form.save()
            return redirect("home:vehicle_detail", vehicle_id=vehicle.id)
    else:
        form = JobSheetForm(instance=job_sheet)
    context = {
        "form": form,
        "vehicle": vehicle,
    }
    return render(request, "home/edit_job_sheet.html", context)


@login_required
@workshop_access_required
def create_internal_estimate(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    EstimatePartFormSet = inlineformset_factory(
        InternalEstimate, EstimatePart, form=EstimatePartForm, extra=1, can_delete=True
    )
    if request.method == "POST":
        form = InternalEstimateForm(request.POST)
        if form.is_valid():
            internal_estimate = form.save(commit=False)
            internal_estimate.vehicle = vehicle
            internal_estimate.save()  # Save the InternalEstimate instance first to get a PK

            formset = EstimatePartFormSet(request.POST, instance=internal_estimate)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Internal Estimate created successfully.")
                return redirect("home:vehicle_detail", vehicle_id=vehicle.id)
            else:
                messages.error(
                    request,
                    "Error creating estimate parts. Please check the form for errors.",
                )
                # If formset is invalid, re-render the form with errors
                # Ensure formset is re-initialized with the instance for rendering
                formset = EstimatePartFormSet(request.POST, instance=internal_estimate)
                context = {
                    "form": form,
                    "part_formset": formset,
                    "vehicle": vehicle,
                }
                return render(request, "home/create_internal_estimate.html", context)
        else:
            messages.error(
                request,
                "Error creating internal estimate. Please check the form for errors.",
            )
            # If form is invalid, re-render the form with errors
            # Re-initialize formset with the unsaved internal_estimate for rendering
            internal_estimate = form.save(
                commit=False
            )  # Get the unsaved instance from the invalid form
            internal_estimate.vehicle = vehicle  # Ensure vehicle is set
            formset = EstimatePartFormSet(request.POST, instance=internal_estimate)
            context = {
                "form": form,
                "part_formset": formset,
                "vehicle": vehicle,
            }
            return render(request, "home/create_internal_estimate.html", context)
    else:
        # For GET request, always create a new unsaved instance for the form
        internal_estimate = InternalEstimate(vehicle=vehicle)
        form = InternalEstimateForm(instance=internal_estimate)
        formset = EstimatePartFormSet(instance=internal_estimate)

    context = {
        "form": form,
        "part_formset": formset,
        "vehicle": vehicle,
    }
    return render(request, "home/create_internal_estimate.html", context)


@login_required
@workshop_access_required
def edit_internal_estimate(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    internal_estimate = InternalEstimate.objects.get(vehicle=vehicle)
    EstimatePartFormSet = inlineformset_factory(
        InternalEstimate, EstimatePart, form=EstimatePartForm, extra=1, can_delete=True
    )
    if request.method == "POST":
        form = InternalEstimateForm(request.POST, instance=internal_estimate)
        if form.is_valid():
            form.save()
            formset = EstimatePartFormSet(request.POST, instance=internal_estimate)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Internal Estimate updated successfully.")
                return redirect("home:vehicle_detail", vehicle_id=vehicle.id)
            else:
                messages.error(
                    request,
                    "Error updating estimate parts. Please check the form for errors.",
                )
        else:
            messages.error(
                request,
                "Error updating internal estimate. Please check the form for errors.",
            )
    else:
        form = InternalEstimateForm(instance=internal_estimate)
        formset = EstimatePartFormSet(instance=internal_estimate)
    context = {
        "form": form,
        "part_formset": formset,
        "vehicle": vehicle,
    }
    return render(request, "home/edit_internal_estimate.html", context)


@login_required
@workshop_access_required
def print_job_sheet(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    job_sheet = JobSheet.objects.get(vehicle=vehicle)

    context = {
        "vehicle": vehicle,
        "job_sheet": job_sheet,
        "date_now": datetime.date.today(),
    }
    return render(request, "home/print_job_sheet.html", context)


def custom_404(request, exception):
    return render(request, "404.html", {}, status=404)


def custom_500(request):
    return render(request, "500.html", {}, status=500)


def custom_403(request, exception):
    return render(request, "403.html", {}, status=403)


def custom_400(request, exception):
    return render(request, "400.html", {}, status=400)
