from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from accounts.models import CustomUser
from workshop.models import Vehicle, JobSheet, InternalEstimate, EstimatePart
from workshop.forms import (
    VehicleForm,
    JobSheetForm,
    InternalEstimateForm,
    EstimatePartForm,
)


@login_required
def dashboard(request):
    return render(request, "home/dashboard.html")


@login_required
def inventory(request):
    return render(request, "home/inventory.html")


@login_required
def sales(request):
    return render(request, "home/sales.html")


@login_required
def staffs(request):
    if request.user.access_level not in ["admin", "manager"]:
        return redirect("home:dashboard")

    users = CustomUser.objects.exclude(access_level="admin")
    context = {"staffs": users}
    return render(request, "home/staffs.html", context)


@login_required
def workshop(request):
    vehicles = Vehicle.objects.all()
    query = request.GET.get("q")
    status = request.GET.get("status")

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
    }
    return render(request, "home/workshop.html", context)


@login_required
def vehicle_detail(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    context = {
        "vehicle": vehicle,
    }
    return render(request, "home/vehicle_detail.html", context)


@login_required
def add_vehicle(request):
    if request.method == "POST":
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("home:workshop")
    else:
        form = VehicleForm()
    context = {
        "form": form,
    }
    return render(request, "home/add_vehicle.html", context)


@login_required
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
def update_vehicle_status(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    if request.method == "POST":
        status = request.POST.get("status")
        if status in [choice[0] for choice in Vehicle.STATUS_CHOICES]:
            vehicle.status = status
            vehicle.save()
    return redirect("home:workshop")


@login_required
def delete_vehicle(request, vehicle_id):
    vehicle = Vehicle.objects.get(id=vehicle_id)
    if request.user.access_level == "admin" or request.user.access_level == "manager":
        vehicle.delete()
    return redirect("home:workshop")


@login_required
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
            internal_estimate.save()
            formset = EstimatePartFormSet(request.POST, instance=internal_estimate)
            if formset.is_valid():
                formset.save()
                return redirect("home:vehicle_detail", vehicle_id=vehicle.id)
    else:
        form = InternalEstimateForm()
        formset = EstimatePartFormSet()
    context = {
        "form": form,
        "part_formset": formset,
        "vehicle": vehicle,
    }
    return render(request, "home/create_internal_estimate.html", context)


@login_required
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
                return redirect("home:vehicle_detail", vehicle_id=vehicle.id)
    else:
        form = InternalEstimateForm(instance=internal_estimate)
        formset = EstimatePartFormSet(instance=internal_estimate)
    context = {
        "form": form,
        "part_formset": formset,
        "vehicle": vehicle,
    }
    return render(request, "home/edit_internal_estimate.html", context)
