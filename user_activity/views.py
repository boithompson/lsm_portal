from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import UserActivityLog
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from accounts.models import CustomUser, Branch # Assuming CustomUser and Branch are in accounts.models

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin, login_url='/permission-denied/') # Redirect to a permission denied page
def log_view(request):
    logs_queryset = UserActivityLog.objects.all()

    # Filters
    user_filter = request.GET.get('user')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    url_query = request.GET.get('url_query')
    branch_filter_pk = request.GET.get('branch') # New branch filter

    if user_filter:
        logs_queryset = logs_queryset.filter(user__email__icontains=user_filter)
    
    if from_date_str:
        try:
            from_date = timezone.make_aware(datetime.strptime(from_date_str, '%Y-%m-%d'))
            logs_queryset = logs_queryset.filter(timestamp__gte=from_date)
        except ValueError:
            pass # Handle invalid date format silently or add a message
    
    if to_date_str:
        try:
            to_date = timezone.make_aware(datetime.strptime(to_date_str, '%Y-%m-%d')) + timedelta(days=1) - timedelta(microseconds=1)
            logs_queryset = logs_queryset.filter(timestamp__lte=to_date)
        except ValueError:
            pass # Handle invalid date format silently or add a message

    if url_query:
        logs_queryset = logs_queryset.filter(Q(url__icontains=url_query) | Q(action_description__icontains=url_query))

    if branch_filter_pk:
        logs_queryset = logs_queryset.filter(user__branch__pk=branch_filter_pk)

    # Pagination
    paginator = Paginator(logs_queryset, 50) # 50 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    branches = Branch.objects.all().order_by('name') # Get all branches for filter dropdown

    context = {
        'page_obj': page_obj,
        'user_filter': user_filter,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'url_query': url_query,
        'branches': branches, # Pass branches to template
        'selected_branch': branch_filter_pk, # Pass selected branch for dropdown
    }
    return render(request, 'user_activity/log.html', context)
