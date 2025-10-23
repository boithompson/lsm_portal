from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from accounts.models import CustomUser, Branch
from workshop.models import Vehicle, JobSheet, InternalEstimate, EstimatePart
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
                return redirect("accounts:login") # Redirect to login if not authenticated
            if request.user.access_level not in ["admin", "workshop", "procurement"]:
                messages.error(request, "You do not have permission to access this page.")
                return redirect("home:dashboard")
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.exception("Error in workshop_access_required decorator:")
            messages.error(request, f"An unexpected error occurred in access check: {e}")
            return redirect("home:dashboard") # Redirect to a safe page
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
            vehicles = Vehicle.objects.all()
            branches = Branch.objects.all()

            if selected_branch_id:
                vehicles = vehicles.filter(branch__id=selected_branch_id)
        else:
            if request.user.branch:
                vehicles = Vehicle.objects.filter(branch=request.user.branch)
            else:
                # If a non-admin user has no branch assigned, they shouldn't see any vehicles
                vehicles = Vehicle.objects.none()
            branches = []  # no need to show branches to non-admins, but provide an empty list

        if query:
            vehicles = vehicles.filter(
                Q(customer_name__icontains=query)
                | Q(vehicle_make__icontains=query)
                | Q(model__icontains=query)
                | Q(licence_plate__icontains=query)
            )

        if status:
            vehicles = vehicles.filter(status=status)

        context = {
            "vehicles": vehicles,
            "vehicle_status_choices": Vehicle.STATUS_CHOICES,
            "branches": branches,  # will be used for filter dropdown in template
            "selected_branch_id": selected_branch_id,
        }
        return render(request, "home/workshop.html", context)
    except Exception as e:
        logger.exception("Error in workshop view:")
        messages.error(request, f"An unexpected error occurred: {e}")
        return redirect("home:dashboard") # Redirect to a safe page


@login_required
@workshop_access_required
def vehicle_detail(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    context = {
        "vehicle": vehicle,
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
            vehicle = form.save(commit=False)

            if request.user.access_level == "admin":
                # Admin-selected branch is included in POST data
                vehicle.branch = form.cleaned_data["branch"]
            else:
                # Auto-assign user's branch
                vehicle.branch = request.user.branch

            vehicle.save()
            messages.success(request, "Vehicle created successfully.")
            return redirect("home:workshop")
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
        if status in [choice[0] for choice in Vehicle.STATUS_CHOICES]:
            vehicle.status = status
            vehicle.save()
    return redirect("home:workshop")


@login_required
@workshop_access_required
def delete_vehicle(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    if request.user.access_level in ["admin", "manager",]:
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
            internal_estimate.save() # Save the InternalEstimate instance first to get a PK

            formset = EstimatePartFormSet(request.POST, instance=internal_estimate)
            if formset.is_valid():
                formset.save()
                messages.success(request, "Internal Estimate created successfully.")
                return redirect("home:vehicle_detail", vehicle_id=vehicle.id)
            else:
                messages.error(request, "Error creating estimate parts. Please check the form for errors.")
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
            messages.error(request, "Error creating internal estimate. Please check the form for errors.")
            # If form is invalid, re-render the form with errors
            # Re-initialize formset with the unsaved internal_estimate for rendering
            internal_estimate = form.save(commit=False) # Get the unsaved instance from the invalid form
            internal_estimate.vehicle = vehicle # Ensure vehicle is set
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
                messages.error(request, "Error updating estimate parts. Please check the form for errors.")
        else:
            messages.error(request, "Error updating internal estimate. Please check the form for errors.")
    else:
        form = InternalEstimateForm(instance=internal_estimate)
        formset = EstimatePartFormSet(instance=internal_estimate)
    context = {
        "form": form,
        "part_formset": formset,
        "vehicle": vehicle,
    }
    return render(request, "home/edit_internal_estimate.html", context)


def custom_404(request, exception):
    return render(request, "404.html", {}, status=404)

def custom_500(request):
    return render(request, "500.html", {}, status=500)

def custom_403(request, exception):
    return render(request, "403.html", {}, status=403)

def custom_400(request, exception):
    return render(request, "400.html", {}, status=400)
