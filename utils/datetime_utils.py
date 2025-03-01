import datetime


def to_milliseconds_from_minutes(minutes):
    return int(minutes) * 60 * 1000

def format_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')