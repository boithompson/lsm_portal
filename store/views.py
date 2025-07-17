from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Inventory
from .forms import InventoryForm
from accounts.models import Branch
from django.db.models import Q
from django.contrib import messages


@login_required
def add_inventory(request):
    # Only allow admin, sales, and manager users
    if request.user.access_level not in ["admin", "sales", "manager"]:
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

    # Only allow access if user is admin, manager, or sales in same branch
    if request.user.access_level not in ["admin", "sales", "manager"]:
        messages.error(request, "You do not have permission to view this inventory.")
        return redirect("store:inventory_list")

    if request.user.access_level != "admin" and inventory.branch != request.user.branch:
        messages.error(request, "You do not have access to this branch's inventory.")
        return redirect("store:inventory_list")

    if request.method == "POST":
        form = InventoryForm(request.POST, request.FILES, instance=inventory, user=request.user)
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

    return render(request, "store/inventory_detail.html", {"form": form, "inventory": inventory})


@login_required
def inventory_list(request):
    inventories = Inventory.objects.all()
    branch_filter = request.GET.get("branch")
    query = request.GET.get("q")

    if request.user.access_level != "admin":
        inventories = inventories.filter(branch=request.user.branch)
    elif branch_filter:
        inventories = inventories.filter(branch_id=branch_filter)

    if query:
        inventories = inventories.filter(
            Q(make__icontains=query)
            | Q(model__icontains=query)
            | Q(vin__icontains=query)
        )

    branches = Branch.objects.all() if request.user.access_level == "admin" else None

    context = {
        "inventories": inventories,
        "branches": branches,
        "selected_branch": branch_filter,
    }
    return render(request, "store/inventory_list.html", context)
