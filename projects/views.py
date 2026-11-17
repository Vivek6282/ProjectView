import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import manager_or_hr_required
from django.views.decorators.cache import never_cache
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
from datetime import date
from .models import Project, ProjectAsset
from .forms import ProjectForm


from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.http import Http404
from projectview.files import validate_uploaded_file, build_safe_file_response

logger = logging.getLogger(__name__)


def can_manage_project(user, project):
    """Check if user is allowed to manage/update project workflow and assets."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    role = getattr(user, 'profile', None).role if hasattr(user, 'profile') else 'employee'
    if role in ['manager', 'hr']:
        return True
    if project.created_by == user:
        return True
    return project.assigned_to.filter(id=user.id).exists()


def can_delete_project_asset(user, asset):
    """Check if user can delete an asset."""
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    role = getattr(user, 'profile', None).role if hasattr(user, 'profile') else 'employee'
    if role in ['manager', 'hr']:
        return True
    return asset.uploaded_by == user or asset.project.created_by == user


@never_cache
@login_required
def project_list_view(request):
    projects = Project.objects.all()

    q = request.GET.get('q', '').strip()
    if q:
        projects = projects.filter(
            Q(title__icontains=q) | Q(details__icontains=q)
        )

    category = request.GET.get('category', '')
    if category:
        projects = projects.filter(category=category)

    status = request.GET.get('status', '')
    if status:
        projects = projects.filter(status=status)

    priority = request.GET.get('priority', '')
    if priority:
        projects = projects.filter(priority=priority)

    tab = request.GET.get('tab', 'all')
    today = date.today()
    if tab == 'upcoming':
        projects = projects.filter(deadline__gte=today).exclude(status='Done')
    elif tab == 'overdue':
        projects = projects.filter(deadline__lt=today).exclude(status='Done')

    sort = request.GET.get('sort', 'deadline_asc')
    if sort == 'deadline_desc':
        projects = projects.order_by('-deadline')
    else:
        projects = projects.order_by('deadline')

    categories = Project.CATEGORY_CHOICES
    statuses = Project.STATUS_CHOICES
    priorities = Project.PRIORITY_CHOICES

    context = {
        'projects': projects,
        'q': q,
        'category': category,
        'status': status,
        'priority': priority,
        'tab': tab,
        'sort': sort,
        'categories': categories,
        'statuses': statuses,
        'priorities': priorities,
        'today': today,
    }
    return render(request, 'projects/project_list.html', context)


@never_cache
@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    can_manage = can_manage_project(request.user, project)
    can_upload = can_manage and project.status != 'Done'
    can_complete = can_manage and project.status != 'Done'
    context = {
        'project': project,
        'can_manage': can_manage,
        'can_upload': can_upload,
        'can_complete': can_complete,
    }
    return render(request, 'projects/project_detail.html', context)


@never_cache
@manager_or_hr_required
def admin_project_list(request):
    projects = Project.objects.all().order_by('-updated_at')
    return render(request, 'dashboard/project_list.html', {'projects': projects})


@never_cache
@manager_or_hr_required
def admin_project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()
            messages.success(request, 'Project created successfully.')
            return redirect('/dashboard/projects/')
    else:
        form = ProjectForm()
    return render(request, 'dashboard/project_create.html', {'form': form})


@never_cache
@manager_or_hr_required
def admin_project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('/dashboard/projects/')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'dashboard/project_edit.html', {'form': form, 'project': project})


@never_cache
@manager_or_hr_required
def admin_project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted.')
        return redirect('/dashboard/projects/')
    return render(request, 'dashboard/project_delete.html', {'project': project})


@never_cache
@login_required
@require_POST
def submit_project_complete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not can_manage_project(request.user, project):
        messages.error(request, 'You do not have permission to mark this project as completed.')
        return redirect('projects:project_detail', pk=pk)

    if project.status != 'Done':
        project.status = 'Done'
        project.completed_at = timezone.now()
        project.save()
        messages.success(request, f'Project "{project.title}" has been submitted as completed.')
    return redirect('projects:project_detail', pk=pk)


@never_cache
@login_required
@require_POST
def upload_project_asset(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not can_manage_project(request.user, project):
        messages.error(request, 'You do not have permission to upload files to this project.')
        return redirect('projects:project_detail', pk=pk)

    if project.status == 'Done':
        messages.error(request, 'Cannot upload files to a completed project.')
        return redirect('projects:project_detail', pk=pk)

    files = request.FILES.getlist('assets')
    if not files:
        messages.error(request, 'No files selected for upload.')
        return redirect('projects:project_detail', pk=pk)

    valid_files = []
    for f in files:
        is_valid, err = validate_uploaded_file(f)
        if not is_valid:
            messages.error(request, f'"{f.name}": {err}')
            return redirect('projects:project_detail', pk=pk)
        valid_files.append(f)

    for f in valid_files:
        ProjectAsset.objects.create(
            project=project,
            file=f,
            name=f.name,
            uploaded_by=request.user
        )

    messages.success(request, f'Successfully uploaded {len(valid_files)} file(s).')
    return redirect('projects:project_detail', pk=pk)


@never_cache
@login_required
@require_POST
def delete_project_asset(request, asset_id):
    asset = get_object_or_404(ProjectAsset, id=asset_id)
    project_id = asset.project.id

    if can_delete_project_asset(request.user, asset):
        try:
            asset.file.delete(save=False)
        except Exception:
            logger.exception("Failed to delete asset file %s from storage for asset ID %s", getattr(asset.file, 'name', 'unknown'), asset.id)
        asset.delete()
        messages.success(request, 'Asset deleted successfully.')
    else:
        messages.error(request, 'Unauthorized to delete this asset.')

    return redirect('projects:project_detail', pk=project_id)


@never_cache
@login_required
@require_GET
def download_project_asset(request, asset_id):
    asset = get_object_or_404(ProjectAsset, id=asset_id)
    if not asset.file:
        raise Http404("Asset file not found.")

    try:
        return build_safe_file_response(asset.file, filename=asset.name, is_image=asset.is_image)
    except Http404:
        messages.error(request, 'The requested file could not be found on the storage server.')
        return redirect('projects:project_detail', pk=asset.project.id)
