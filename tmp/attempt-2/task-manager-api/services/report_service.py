"""Statistics and reports that aggregate tasks, users and categories."""
from datetime import timedelta

from config.constants import (HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_CANCELLED,
                              STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING, TASK_STATUSES)
from models import Category, Task, User
from utils.time import utc_now


def percentage(part, total):
    return round((part / total) * 100, 2) if total > 0 else 0


def _status_counts():
    counts = Task.count_by_status()
    return {status: counts.get(status, 0) for status in TASK_STATUSES}


def task_stats():
    by_status = _status_counts()
    total = Task.count()
    now = utc_now()
    overdue = sum(1 for task in Task.overdue_candidates() if task.is_overdue(now))
    return {
        'total': total,
        'pending': by_status[STATUS_PENDING],
        'in_progress': by_status[STATUS_IN_PROGRESS],
        'done': by_status[STATUS_DONE],
        'cancelled': by_status[STATUS_CANCELLED],
        'overdue': overdue,
        'completion_rate': percentage(by_status[STATUS_DONE], total),
    }


def summary_report():
    now = utc_now()
    by_priority = Task.count_by_priority()
    overdue_tasks = [task for task in Task.overdue_candidates() if task.is_overdue(now)]
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    totals_by_user = Task.totals_by_user()

    user_productivity = []
    for user in User.all():
        total, completed = totals_by_user.get(user.id, (0, 0))
        user_productivity.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count(),
            'total_users': User.count(),
            'total_categories': Category.count(),
        },
        'tasks_by_status': _status_counts(),
        'tasks_by_priority': {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [{
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': task.days_overdue(now),
            } for task in overdue_tasks],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_completed_since(since),
        },
        'user_productivity': user_productivity,
    }


def user_report(user):
    tasks = Task.for_user(user.id)
    now = utc_now()
    by_status = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    total = len(tasks)
    return {
        'user': user.to_public_dict(),
        'statistics': {
            'total_tasks': total,
            'done': by_status[STATUS_DONE],
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'cancelled': by_status[STATUS_CANCELLED],
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': percentage(by_status[STATUS_DONE], total),
        },
    }
