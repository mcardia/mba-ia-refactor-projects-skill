"""Statistics and reports that aggregate several models."""
from datetime import timedelta

from config.constants import (HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS,
                              STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING,
                              TASK_STATUSES)
from models.category import Category
from models.task import Task
from models.user import User
from utils.time import utc_now


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def _status_breakdown(counts):
    return {status: counts.get(status, 0) for status in TASK_STATUSES}


def task_stats():
    total = Task.count_all()
    by_status = _status_breakdown(Task.count_by_status())
    overdue = len(Task.list_overdue(utc_now()))
    return {
        'total': total,
        **by_status,
        'overdue': overdue,
        'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
    }


def summary_report():
    now = utc_now()
    by_priority = Task.count_by_priority()
    overdue_tasks = Task.list_overdue(now)
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    totals_by_user = Task.count_by_user()
    done_by_user = Task.count_done_by_user()
    user_productivity = []
    for user in User.list_all():
        total = totals_by_user.get(user.id, 0)
        completed = done_by_user.get(user.id, 0)
        user_productivity.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': _status_breakdown(Task.count_by_status()),
        'tasks_by_priority': {label: by_priority.get(priority, 0)
                              for priority, label in PRIORITY_LABELS.items()},
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
            'tasks_completed_last_7_days': Task.count_done_since(since),
        },
        'user_productivity': user_productivity,
    }


def user_report(user):
    tasks = Task.list_by_user(user.id)
    now = utc_now()
    by_status = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': by_status[STATUS_DONE],
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'cancelled': by_status[STATUS_CANCELLED],
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': calculate_percentage(by_status[STATUS_DONE], total),
        },
    }
