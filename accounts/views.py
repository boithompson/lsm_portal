from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, StaffCreationForm, StaffEditForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        if request.user.access_level in ['workshop', 'procurement']:
            return redirect("home:workshop")
        else:
            return redirect("home:dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                if user.access_level in ['workshop', 'procurement']:
                    return redirect("home:workshop")
                else:
                    return redirect("home:dashboard")
            else:
                form.add_error(None, "Invalid credentials")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")


@login_required
def add_staff(request):
    # Only admin and manager can access
    if request.user.access_level not in ["admin", "manager"]:
        messages.error(request, "You do not have permission to add staff.")
        return redirect("home:dashboard")

    if request.method == "POST":
        form = StaffCreationForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)

            # Admin can assign any branch manually (optional to add dropdown)
            # Manager must auto-assign their own branch to the new staff
            if request.user.access_level == "manager":
                user.branch = request.user.branch

            password = form.cleaned_data.get("password")
            user.set_password(password)
            user.save()
            messages.success(request, "Staff created successfully.")
            return redirect("home:staffs")
    else:
        form = StaffCreationForm(user=request.user)

    return render(request, "accounts/add_staff.html", {"form": form})


@login_required
def edit_staff(request, user_id):
    if request.user.access_level not in ["admin", "manager"]:
        messages.error(request, "You do not have permission to edit staff.")
        return redirect("home:dashboard")

    staff_member = get_object_or_404(CustomUser, id=user_id)

    # Managers cannot edit other managers or themselves
    if request.user.access_level == "manager":
        if staff_member.access_level == "manager" or staff_member.id == request.user.id:
            messages.error(
                request, "Managers cannot edit other managers or their own details."
            )
            return redirect("home:staffs")

    if request.method == "POST":
        form = StaffEditForm(request.POST, instance=staff_member, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff details updated successfully.")
            return redirect("home:staffs")
    else:
        form = StaffEditForm(instance=staff_member, user=request.user)

    return render(
        request,
        "accounts/edit_staff.html",
        {"form": form, "staff_member": staff_member},
    )


@login_required
def delete_staff(request, user_id):
    if request.user.access_level not in ["admin", "manager"]:
        return redirect("home:dashboard")

    staff_member = get_object_or_404(CustomUser, id=user_id)
    staff_member.delete()
    return redirect("home:staffs")
