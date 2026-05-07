from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import manager_or_hr_required
from django.views.decorators.cache import never_cache
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Q
from datetime import date
from .models import Project
from .forms import ProjectForm


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
    return render(request, 'projects/project_detail.html', {'project': project})


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
