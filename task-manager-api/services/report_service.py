"""Reporting and statistics use cases (aggregations across tasks, users and categories)."""
from datetime import timedelta

from config.constants import (
    HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_CANCELLED,
    STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING,
)
from models.category import Category
from models.task import Task
from models.user import User
from utils.time import utc_now


def percentage(part, total):
    return round((part / total) * 100, 2) if total > 0 else 0


def _status_counts(counts):
    return {status: counts.get(status, 0)
            for status in (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)}


def task_stats():
    total = Task.count_all()
    by_status = _status_counts(Task.count_by_status())
    return {
        'total': total,
        **by_status,
        'overdue': Task.count_overdue(utc_now()),
        'completion_rate': percentage(by_status[STATUS_DONE], total),
    }


def _user_productivity(users):
    counts = Task.count_by_user_and_status()
    totals, completed = {}, {}
    for (user_id, status), count in counts.items():
        totals[user_id] = totals.get(user_id, 0) + count
        if status == STATUS_DONE:
            completed[user_id] = completed.get(user_id, 0) + count
    stats = []
    for user in users:
        total = totals.get(user.id, 0)
        done = completed.get(user.id, 0)
        stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': percentage(done, total),
        })
    return stats


def summary():
    now = utc_now()
    users = User.list_all()
    by_priority = Task.count_by_priority()
    overdue_tasks = Task.list_overdue(now)
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': len(users),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': _status_counts(Task.count_by_status()),
        'tasks_by_priority': {label: by_priority.get(priority, 0)
                              for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [{
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (now - task.due_date).days,
            } for task in overdue_tasks],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_completed_since(since),
        },
        'user_productivity': _user_productivity(users),
    }


def user_report(user):
    tasks = Task.list_by_user(user.id)
    now = utc_now()
    by_status = _status_counts({})
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **by_status,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks
                                 if task.priority is not None and task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': percentage(by_status[STATUS_DONE], total),
        },
    }
