import datetime


def calculate_working_hours(enter_time, exit_time, break_time):
    if type(enter_time) is str:
        enter_time = datetime.datetime.strptime(enter_time, '%Y-%m-%d %H:%M:%S')

    if type(exit_time) is str:
        exit_time = datetime.datetime.strptime(exit_time, '%Y-%m-%d %H:%M:%S')
    diff_time = exit_time - enter_time
    diff_sec = diff_time.total_seconds()
    break_time = float(break_time)
    hours = float(int(diff_sec/3600) - abs(break_time))
    minutes = float((int(diff_sec/60) % 60) / 60)
    total_hours = round(hours + minutes, 2)
    return total_hours


def get_real_name(user):
    name = user.korean_name + '님'
    return name


def get_this_monday(today_date):
    # DEPRECATED
    monday = today_date - datetime.timedelta(days=today_date.weekday())
    return monday


def get_week_data(queryset):
    last_date = queryset.last().entered_time.date()
    week_data = {}
    for no in range(last_date.weekday()+1):
        num = last_date.weekday() - no
        week_data[no] = get_days_data(num, last_date, queryset)
    total = 0
    for val in week_data.values():
        if val:
            total += val
    total = round(total, 2)
    week_data['total'] = total
    return week_data


def get_days_data(delta, today, queryset):
    aim_date = today - datetime.timedelta(delta)
    logs = []
    for q in queryset:
        if q.entered_time.date() == aim_date:
            logs.append(q)
    hours = 0
    for log in logs:
        if not log.exited_time:
            return None
        enter_time = log.entered_time
        exit_time = log.exited_time
        b_time = log.break_hours
        hour = calculate_working_hours(enter_time, exit_time, b_time)
        hours += hour
    return hours
