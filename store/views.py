from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Inventory
from .forms import InventoryForm
from accounts.models import Branch
from django.db.models import Q


@login_required
def add_inventory(request):
    if request.method == "POST":
        form = InventoryForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            inventory = form.save(commit=False)

            # For non-admins, assign branch automatically
            if request.user.access_level != "admin":
                inventory.branch = request.user.branch

            inventory.save()
            return redirect("store:inventory_list")
    else:
        form = InventoryForm(user=request.user)

    return render(request, "store/add_inventory.html", {"form": form})


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
