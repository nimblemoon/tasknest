"""
Shared helper functions for the tasks app.

Factored out here (rather than duplicated across views) per the
"reasonable modularity" requirement in the project spec (Section 8).
"""

# Maps priority string -> numeric weight, used to sort "highest priority first".
_PRIORITY_WEIGHT = {'high': 3, 'medium': 2, 'low': 1}


def apply_task_filters(queryset, status=None, priority=None, sort=None):
    """Filter and sort a Task queryset based on dashboard/filter-view inputs.

    Args:
        queryset: base QuerySet of Task objects (already scoped to the owner).
        status: '' | 'pending' | 'completed'
        priority: '' | 'low' | 'medium' | 'high'
        sort: 'due_date' (default) | '-priority'

    Returns:
        A filtered, ordered QuerySet.
    """
    if status == 'pending':
        queryset = queryset.filter(is_complete=False)
    elif status == 'completed':
        queryset = queryset.filter(is_complete=True)

    if priority in ('low', 'medium', 'high'):
        queryset = queryset.filter(priority=priority)

    if sort == '-priority':
        # Django can't sort TextChoices by custom weight directly in SQLite
        # without a Case/When, so build that ordering expression here.
        from django.db.models import Case, When, IntegerField

        queryset = queryset.annotate(
            _priority_weight=Case(
                *[When(priority=key, then=value) for key, value in _PRIORITY_WEIGHT.items()],
                output_field=IntegerField(),
            )
        ).order_by('-_priority_weight', 'due_date')
    else:
        queryset = queryset.order_by('due_date')

    return queryset
