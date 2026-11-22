from datetime import datetime, timezone


def utc_now():
    """Naive UTC datetime (what the deprecated datetime.utcnow() returned).

    Naive values keep comparisons valid against rows already stored without timezone.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
