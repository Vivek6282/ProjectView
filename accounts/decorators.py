from django.core.exceptions import PermissionDenied
from functools import wraps

def hr_required(view_func):
    """Decorator for views that require the HR role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if hasattr(request.user, 'profile') and request.user.profile.role == 'hr':
                return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def manager_or_hr_required(view_func):
    """Decorator for views that require either Manager or HR role."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if hasattr(request.user, 'profile') and request.user.profile.role in ['manager', 'hr']:
                return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view
