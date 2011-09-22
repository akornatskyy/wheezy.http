
""" ``datetime`` module.
"""

from datetime import datetime
from datetime import timedelta
from datetime import tzinfo
from time import gmtime
from time import mktime


ZERO = timedelta(0)
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = (None, "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def format_http_datetime(stamp):
    """ Format datetime to a string following rfc1123 pattern.

        >>> from datetime import datetime
        >>> now = datetime(2011, 9, 19, 10, 45, 30, 0, UTC)
        >>> format_http_datetime(now)
        'Mon, 19 Sep 2011 10:45:30 GMT'
        >>> format_http_datetime(100) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeError: ...
    """
    if isinstance(stamp, datetime):
        if stamp.tzinfo:
            stamp = stamp.astimezone(UTC).timetuple()
        else:  # pragma: nocover
            # TODO: the output depends on local timezone
            stamp = gmtime(mktime(stamp.timetuple()))
    else:
        raise TypeError('Expecting type ``datetime.datetime``.')

    year, month, day, hh, mm, ss, wd, y, z = stamp
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
        WEEKDAYS[wd], day, MONTHS[month], year, hh, mm, ss
    )


def total_seconds(delta):
    """ Returns a total number of seconds for the given delta.

        ``delta`` can be ``datetime.timedelta``.

        >>> total_seconds(timedelta(hours=2))
        7200

        or int:

        >>> total_seconds(100)
        100

        otherwise raise ``TypeError``.

        >>> total_seconds('100') # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeError: ...
    """
    if isinstance(delta, int):
        return delta
    elif isinstance(delta, timedelta):
        return delta.seconds + delta.days * 86400
    else:
        raise TypeError('Expecting type datetime.timedelta '
            'or int for seconds')


class utc(tzinfo):
    """ UTC timezone.

    """

    def tzname(self, dt):
        """ Name of time zone.

            >>> UTC.tzname(None)
            'UTC'
        """
        return 'UTC'

    def utcoffset(self, dt):
        """ Offset from UTC.

            >>> UTC.utcoffset(None)
            datetime.timedelta(0)
        """
        return ZERO

    def dst(self, dt):
        """ DST is not in effect.

            >>> UTC.dst(None)
            datetime.timedelta(0)
        """
        return ZERO


GMT = UTC = utc()
