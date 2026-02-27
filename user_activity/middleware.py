from .models import UserActivityLog
from django.urls import reverse
from django.utils import timezone
import re


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log activity for authenticated users, excluding static/media files and admin logs page itself
        if (
            request.user.is_authenticated
            and not request.path.startswith(reverse("admin:index"))
            and not request.path.startswith(reverse("user_activity:log_view"))
        ):
            # Exclude static and media files
            if not (
                request.path.startswith("/static/")
                or request.path.startswith("/media/")
            ):
                # Generate human-readable description
                description = self.generate_description(request)
                
                UserActivityLog.objects.create(
                    user=request.user,
                    url=request.path,
                    method=request.method,
                    timestamp=timezone.now(),
                    action_description=description
                )
        return response

    def generate_description(self, request):
        """Generate human-readable descriptions for different URL patterns"""
        path = request.path
        
        # Vehicle-related actions
        if re.match(r'^/dashboard/vehicle/add/$', path):
            return "Added a new vehicle record"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/$', path):
            return "Viewed vehicle details"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/edit/$', path):
            return "Edited vehicle information"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/delete/$', path):
            return "Deleted vehicle record"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/job_sheet/create/$', path):
            return "Created a new job sheet"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/job_sheet/edit/$', path):
            return "Edited job sheet"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/internal_estimate/create/$', path):
            return "Created internal estimate"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/internal_estimate/edit/$', path):
            return "Edited internal estimate"
        
        elif re.match(r'^/dashboard/vehicle/(\d+)/job_sheet/print/$', path):
            return "Printed job sheet"
        
        elif re.match(r'^/dashboard/chasis-lookup/$', path):
            return "Performed chasis number lookup"
        
        # Staff management actions
        elif re.match(r'^/accounts/staffs/add/$', path):
            return "Added new staff member"
        
        elif re.match(r'^/accounts/staffs/edit/(\d+)/$', path):
            return "Edited staff member details"
        
        elif re.match(r'^/accounts/staffs/delete/(\d+)/$', path):
            return "Deleted staff member"
        
        # Store actions
        elif re.match(r'^/store/add-stock/$', path):
            return "Added new stock item"
        
        elif re.match(r'^/store/central/add-stock/$', path):
            return "Added central stock item"
        
        elif re.match(r'^/store/sales/create/$', path):
            return "Created sales record"
        
        elif re.match(r'^/store/sales/export/$', path):
            return "Exported sales data"
        
        elif re.match(r'^/store/stock/export/$', path):
            return "Exported stock data"
        
        # Workshop actions
        elif re.match(r'^/workshop/export/$', path):
            return "Exported workshop data"
        
        # Default fallback
        else:
            # For unmatched patterns, provide a generic description
            if request.method == 'GET':
                return f"Viewed {self.get_page_name(path)}"
            elif request.method == 'POST':
                return f"Submitted form on {self.get_page_name(path)}"
            else:
                return f"Performed {request.method} action on {self.get_page_name(path)}"

    def get_page_name(self, path):
        """Extract meaningful page name from URL path"""
        # Remove leading slash and split by '/'
        parts = path.strip('/').split('/')
        
        if not parts or parts[0] == '':
            return "Home page"
        
        # Map common URL patterns to readable names
        page_names = {
            'dashboard': 'Dashboard',
            'workshop': 'Workshop',
            'store': 'Store',
            'accounts': 'Accounts',
            'user_activity': 'User Activity',
            'chasis-lookup': 'Chasis Lookup',
            'add-stock': 'Add Stock',
            'sales': 'Sales',
            'export': 'Export',
            'staffs': 'Staff Management',
            'add': 'Add',
            'edit': 'Edit',
            'delete': 'Delete',
            'create': 'Create',
            'print': 'Print',
        }
        
        # Return the most relevant part of the path
        for part in parts:
            if part in page_names:
                return page_names[part]
        
        # If no match found, return the first part capitalized
        return parts[0].replace('-', ' ').title()
