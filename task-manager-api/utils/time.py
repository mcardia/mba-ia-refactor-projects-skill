from datetime import datetime, timezone


def utc_now():
    """Naive UTC datetime: the value datetime.utcnow() returned, without the deprecated call.

    Naive values keep comparisons valid against rows already stored without timezone.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
