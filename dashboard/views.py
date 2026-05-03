from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.db.models import Count, Q
from django.http import JsonResponse
from projects.models import Project
from datetime import date, timedelta


@never_cache
@staff_member_required
def dashboard_view(request):
    today = date.today()
    projects = Project.objects.all()

    stats = {
        'total': projects.count(),
        'upcoming': projects.filter(deadline__gte=today).exclude(status='Done').count(),
        'overdue': projects.filter(deadline__lt=today).exclude(status='Done').count(),
        'completed': projects.filter(status='Done').count(),
    }

    return render(request, 'dashboard/dashboard.html', {'stats': stats})


@never_cache
@staff_member_required
def analytics_json(request):
    today = date.today()
    projects = Project.objects.all()

    by_category = list(projects.values('category').annotate(count=Count('id')).order_by('-count'))
    by_status = list(projects.values('status').annotate(count=Count('id')))
    by_priority = list(projects.values('priority').annotate(count=Count('id')))
    by_user = list(projects.values('created_by__username').annotate(count=Count('id')).order_by('-count'))

    prio_status = []
    for prio in ['Low', 'Medium', 'High']:
        counts = projects.filter(priority=prio).values('status').annotate(count=Count('id'))
        status_dict = {s['status']: s['count'] for s in counts}
        prio_status.append({
            'priority': prio,
            'Planned': status_dict.get('Planned', 0),
            'In Progress': status_dict.get('In Progress', 0),
            'Done': status_dict.get('Done', 0),
        })

    velocity = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=i*30)
        first_day = month_date.replace(day=1)
        if month_date.month == 12:
            last_day = month_date.replace(year=month_date.year+1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = month_date.replace(month=month_date.month+1, day=1) - timedelta(days=1)
        
        count = projects.filter(status='Done', completed_at__date__range=[first_day, last_day]).count()
        velocity.append({'month': first_day.strftime('%b'), 'count': count})

    end_date = today + timedelta(days=30)
    deadlines = list(projects.filter(deadline__range=[today, end_date]).values('deadline').annotate(count=Count('id')).order_by('deadline'))

    overdue_trend = []
    for i in range(4, -1, -1):
        week_start = today - timedelta(weeks=i)
        count = projects.filter(deadline__lt=week_start).exclude(status='Done', completed_at__lt=week_start).count()
        overdue_trend.append({'week': week_start.isoformat(), 'count': count})

    data = {
        'today': today.isoformat(),
        'by_category': by_category,
        'by_status': by_status,
        'by_priority': by_priority,
        'by_user': by_user,
        'prio_status': prio_status,
        'velocity': velocity,
        'deadlines_30': deadlines,
        'overdue_trend': overdue_trend,
    }
    return JsonResponse(data)
