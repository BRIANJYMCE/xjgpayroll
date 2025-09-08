from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .forms import WorkAssignmentForm, WorkTypeForm, AdminWorkAssignmentForm, AdminSingleWorkAssignmentForm
from django.db.models import F, ExpressionWrapper, DurationField
from django.db.models import Min, Max, F, Q
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
from django import forms  
from django.contrib import messages
from django.utils.timezone import localtime, now
from django.db.models import Sum, F, ExpressionWrapper, DurationField
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.core.paginator import Paginator


from .models import WorkAssignment, WorkType, WeeklyPayroll
from user_account.models import TimeLog  # import TimeLog
from accounts.models import Profile

User = get_user_model()

# Only superusers can assign tasks
def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@superuser_required
def assign_task(request):
    if request.method == "POST":
        form = WorkAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("task_list")
    else:
        form = WorkAssignmentForm()

    return render(request, "admin_account/assign_task.html", {"form": form})

@superuser_required
def task_list(request):
    # Get filter values
    date_filter = request.GET.get("date_filter")
    work_type_filter = request.GET.get("work_type_filter")
    status_filter = request.GET.get("status_filter")  # "ongoing" or "done"

    # Base queryset
    logs = TimeLog.objects.select_related("user", "task").order_by("-time_in")

    # Filter by date (use datetime.date)
    if date_filter:
        try:
            parsed_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(parsed_date, datetime.min.time()))
            end_dt = timezone.make_aware(datetime.combine(parsed_date, datetime.max.time()))
            logs = logs.filter(time_in__gte=start_dt, time_in__lte=end_dt)
        except ValueError:
            logs = logs.none()


    # Filter by work type
    if work_type_filter:
        logs = logs.filter(work_type_names__icontains=work_type_filter)

    # Filter by status
    if status_filter == "ongoing":
        logs = logs.filter(time_out__isnull=True)
    elif status_filter == "done":
        logs = logs.filter(time_out__isnull=False)

    timelogs = []
    all_timelogs_dates = set()
    all_work_types = set()

    for log in logs:
        if log.time_out is None and log.task and not log.task.work_types.filter(is_active=True).exists():
            continue

        work_types = log.work_type_names or "No type"
        local_in = timezone.localtime(log.time_in) if log.time_in else None
        local_out = timezone.localtime(log.time_out) if log.time_out else None

        # Track unique values for dropdowns
        if local_in:
            all_timelogs_dates.add(local_in.date())
        if log.work_type_names:
            all_work_types.add(log.work_type_names)
        elif log.task and log.task.work_types.exists():
            all_work_types.update([wt.name for wt in log.task.work_types.all()])

        total_hours = None
        if local_in and local_out:
            delta = local_out - local_in
            total_hours = round(delta.total_seconds() / 3600, 2)

        timelogs.append({
            "id": log.id,
            "user": log.user.username,
            "date": local_in.date() if local_in else "",
            "time_in": local_in.strftime("%I:%M %p") if local_in else "",
            "time_out": local_out.strftime("%I:%M %p") if local_out else "",
            "status": "Done" if local_out else "Ongoing",
            "work_types": work_types,
            "total_hours": f"{total_hours} hrs" if total_hours is not None else "Ongoing",
        })

    # Pagination
    paginator = Paginator(timelogs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "all_timelogs_dates": sorted(all_timelogs_dates, reverse=True),
        "all_work_types": sorted(all_work_types),
        "request": request,  # preserve filter values in template
    }
    return render(request, "admin_account/task_list.html", context)

def stop_shift(request, log_id):
    log = get_object_or_404(TimeLog, id=log_id)
    if request.method == "POST":
        log.time_out = timezone.now()
        log.save()

    # Preserve referrer query parameters and anchor
    referrer = request.META.get('HTTP_REFERER')
    if referrer:
        return redirect(referrer)
    return redirect('task_list')


def delete_shift(request, log_id):
    log = get_object_or_404(TimeLog, id=log_id)
    if request.method == "POST":
        log.delete()

    # Preserve referrer query parameters and anchor
    referrer = request.META.get('HTTP_REFERER')
    if referrer:
        return redirect(referrer)
    return redirect('task_list')


@superuser_required
def admin_main_menu(request):
    return render(request, "admin_account/main_menu.html")

@superuser_required
def worktype_options(request):
    if request.method == 'POST':
        form = WorkTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('worktype_options')
    else:
        form = WorkTypeForm()

    # 👇 only fetch active worktypes
    worktypes = WorkType.objects.filter(is_active=True)

    return render(request, 'admin_account/options.html', {
        'form': form,
        'worktypes': worktypes
    })

@superuser_required
def worktype_edit(request, pk):
    worktype = get_object_or_404(WorkType, pk=pk)
    if request.method == 'POST':
        form = WorkTypeForm(request.POST, instance=worktype)
        if form.is_valid():
            form.save()
            return redirect('worktype_options')
    else:
        form = WorkTypeForm(instance=worktype)
    return render(request, 'admin_account/options_edit.html', {'form': form, 'worktype': worktype})

@superuser_required
def worktype_delete(request, pk):
    worktype = get_object_or_404(WorkType, pk=pk)

    # Get ongoing logs + users
    ongoing_logs = TimeLog.objects.filter(
        task__work_types=worktype,
        time_out__isnull=True
    ).select_related("user")

    if request.method == "POST":
        worktype.is_active = False
        worktype.save()
        return redirect("worktype_options")

    # If there are ongoing logs -> show confirmation page with names
    if ongoing_logs.exists():
        users = [log.user.username for log in ongoing_logs]
        return render(request, "admin_account/worktype_confirm_delete.html", {
            "worktype": worktype,
            "users": users
        })

    # If no ongoing logs -> just archive immediately
    worktype.is_active = False
    worktype.save()
    return redirect("worktype_options")


@superuser_required
def manage_users(request):
    # Get filter & sort parameters
    account_filter = request.GET.get("account_filter")
    work_filter = request.GET.get("work_filter")
    sort_order = request.GET.get("sort", "asc")  # default ascending
    name_search = request.GET.get("name_search", "").strip().lower()

    users = User.objects.filter(is_superuser=False)

    user_list = []
    for u in users:
        active_tasks = WorkAssignment.objects.filter(user=u, work_types__is_active=True)
        ongoing_logs = TimeLog.objects.filter(user=u, time_out__isnull=True)

        # Work status
        if ongoing_logs.exists():
            work_status = "On-going"
        elif active_tasks.exists():
            work_status = "Standby"
        else:
            work_status = "Unassigned"

        # Account status
        account_status = "Active" if u.is_active else "Deactivated"

        # Apply name search filter
        if name_search and name_search not in u.username.lower():
            continue

        user_list.append({
            "user": u,
            "work_status": work_status,
            "account_status": account_status
        })

    # Apply filters
    if account_filter:
        user_list = [u for u in user_list if u["account_status"] == account_filter]
    if work_filter:
        user_list = [u for u in user_list if u["work_status"] == work_filter]

    # Sort by username
    reverse = True if sort_order == "desc" else False
    user_list.sort(key=lambda x: x["user"].username.lower(), reverse=reverse)

    # Pagination
    paginator = Paginator(user_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "account_filter": account_filter,
        "work_filter": work_filter,
        "sort_order": sort_order,
        "name_search": name_search
    }

    return render(request, "admin_account/manage_user.html", context)

@superuser_required
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    # Fetch or create profile
    profile, _ = Profile.objects.get_or_create(user=user)

    # --------------------------
    # ACTIVE ASSIGNED WORKTYPES
    # --------------------------
    assigned_worktypes = []
    for wt in WorkType.objects.filter(
        assignments__user=user,
        assignments__logs_is_active_in_user=True,
        is_active=True
    ).distinct():

        has_active_log = TimeLog.objects.filter(
            user=user,
            time_out__isnull=True,
            task__work_types=wt
        ).exists()

        assigned_worktypes.append({
            "id": wt.id,
            "name": wt.name,
            "has_active_log": has_active_log,
        })

    # --------------------------
    # HANDLE POST REQUESTS
    # --------------------------
    if request.method == "POST":

        # ----- DEACTIVATE USER -----
        if "deactivate_account" in request.POST:
            user.is_active = False
            user.save()
            TimeLog.objects.filter(user=user, time_out__isnull=True).update(time_out=timezone.now())
            messages.success(request, f"User {user.username} has been deactivated.")
            return redirect("admin_user_detail", user_id=user.id)

        # ----- DELETE ACCOUNT -----
        elif "delete_account" in request.POST:
            TimeLog.objects.filter(user=user).delete()
            WorkAssignment.objects.filter(user=user).delete()
            username = user.username
            user.delete()
            messages.success(request, f"User {username} and all associated logs have been deleted.")
            return redirect("manage_users")

        # ----- REACTIVATE USER -----
        elif "reactivate_account" in request.POST:
            user.is_active = True
            user.save()
            messages.success(request, f"User {user.username} has been reactivated.")
            return redirect("admin_user_detail", user_id=user.id)

        # ----- REMOVE WORKTYPE -----
        elif "remove_worktype" in request.POST:
            wt_id = request.POST.get("remove_worktype")
            if wt_id:
                try:
                    worktype = WorkType.objects.get(id=wt_id)

                    # Check for active log with this worktype
                    active_log = TimeLog.objects.filter(
                        user=user,
                        time_out__isnull=True,
                        task__work_types=worktype
                    ).first()

                    if active_log:
                        messages.error(
                            request,
                            f"Cannot remove {worktype.name} while user has an active log in it."
                        )
                    else:
                        # Remove work type from current WorkAssignment if exists
                        assignments = WorkAssignment.objects.filter(
                            user=user,
                            work_types=worktype,
                            logs_is_active_in_user=True
                        )
                        for assignment in assignments:
                            assignment.work_types.remove(worktype)
                            if assignment.work_types.count() == 0:
                                assignment.logs_is_active_in_user = False
                            assignment.save()

                        messages.success(
                            request,
                            f"{worktype.name} removed from {user.username}."
                        )

                except WorkType.DoesNotExist:
                    messages.error(request, "Work type does not exist.")

            return redirect("admin_user_detail", user_id=user.id)

        # ----- ASSIGN NEW WORKTYPE -----
        elif "assign_worktype" in request.POST:
            form = AdminSingleWorkAssignmentForm(request.POST, user=user)
            if form.is_valid():
                worktype = form.cleaned_data["work_type"]

                # Get existing assignment or create one
                assignment = WorkAssignment.objects.filter(user=user).first()
                if not assignment:
                    assignment = WorkAssignment.objects.create(user=user)

                # Add the work type only if not already assigned
                if worktype not in assignment.work_types.all():
                    assignment.work_types.add(worktype)
                    assignment.logs_is_active_in_user = True
                    assignment.save()

                messages.success(request, f"{worktype.name} assigned to {user.username}.")
                return redirect("admin_user_detail", user_id=user.id)
        else:
            form = AdminSingleWorkAssignmentForm(user=user)
    else:
        form = AdminSingleWorkAssignmentForm(user=user)

    # --------------------------
    # TIME LOGS (HISTORICAL + ONGOING)
    # --------------------------
    logs = TimeLog.objects.filter(user=user).select_related("task").order_by("-time_in")

    # --------------------------
    # FILTERING
    # --------------------------
    date_filter = request.GET.get("date_filter")
    work_type_filter = request.GET.get("work_type_filter")

    # Build all work types from user's logs for dropdown
    all_work_types = set()
    for log in logs:
        if getattr(log, "work_type_names", None):
            all_work_types.add(log.work_type_names)

    # Apply filters
    if date_filter:
        try:
            logs = logs.filter(time_in__date=date_filter)
        except ValueError:
            pass

    if work_type_filter:
        logs = logs.filter(work_type_names__icontains=work_type_filter)

    # --------------------------
    # Prepare timelog data
    # --------------------------
    timelogs = []
    for log in logs:
        work_types = log.work_type_names or "No type"

        time_in_str, time_out_str, total_hours = "", "", None
        if log.time_in:
            time_in_str = localtime(log.time_in).strftime("%I:%M %p")
        if log.time_out:
            time_out_str = localtime(log.time_out).strftime("%I:%M %p")
            total_hours = round((log.time_out - log.time_in).total_seconds() / 3600, 2)

        timelogs.append({
            "id": log.id,
            "date": localtime(log.time_in).date() if log.time_in else "",
            "time_in": time_in_str,
            "time_out": time_out_str,
            "work_types": work_types,
            "total_hours": f"{total_hours} hrs" if total_hours is not None else "Ongoing",
        })

    # --------------------------
    # PAGINATION (5 logs per page)
    # --------------------------
    paginator = Paginator(timelogs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # --------------------------
    # RENDER CONTEXT
    # --------------------------
    context = {
        "selected_user": user,
        "profile": profile,
        "assigned_worktypes": assigned_worktypes,
        "form": form,
        "page_obj": page_obj,
        "date_filter": date_filter,
        "work_type_filter": work_type_filter,
        "all_work_types": sorted(all_work_types),  # ✅ for dropdown
    }

    return render(request, "admin_account/admin_user_detail.html", context)



@superuser_required
def user_week_list(request, user_id):
    user = get_object_or_404(User, id=user_id)
    logs = TimeLog.objects.filter(user=user, time_out__isnull=False).order_by("time_in")

    # If user has no logs, just return an empty context
    if not logs.exists():
        return render(request, "admin_account/user_week_list.html", {
            "selected_user": user,
            "page_obj": None,
            "all_weeks": [],
        })

    # Get first and last dates
    first_log_date = logs.first().time_in.date()
    today = now().date()
    start_of_first_week = first_log_date - timedelta(days=first_log_date.weekday())
    last_sunday = today - timedelta(days=today.weekday() + 1)

    # Build all weeks
    all_weeks = []
    current_start = start_of_first_week

    while current_start <= last_sunday:
        current_end = current_start + timedelta(days=6)

        # Does this week have logs?
        has_logs = logs.filter(
            time_in__date__gte=current_start,
            time_in__date__lte=current_end
        ).exists()

        # Get payroll record (may be None)
        payroll = WeeklyPayroll.objects.filter(
            user=user,
            week_start=current_start
        ).first()

        all_weeks.append({
            "start": current_start,
            "end": current_end,
            "has_logs": has_logs,
            "payroll": payroll,  # either object or None
        })

        current_start += timedelta(days=7)

    # Sort newest first
    all_weeks = sorted(all_weeks, key=lambda w: w["start"], reverse=True)

    # Paginate
    paginator = Paginator(all_weeks, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "admin_account/user_week_list.html", {
        "selected_user": user,
        "page_obj": page_obj,
        "all_weeks": all_weeks,
    })
    
@superuser_required
def user_weekly_summary(request, user_id, week_start):
    user = get_object_or_404(User, id=user_id)
    start_of_week = datetime.strptime(week_start, "%Y-%m-%d").date()
    end_of_week = start_of_week + timedelta(days=6)
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Fetch logs for display
    logs = TimeLog.objects.filter(
        user=user,
        time_in__date__gte=start_of_week,
        time_in__date__lte=end_of_week,
        time_out__isnull=False
    ).order_by("time_in")

    # Prepare daily summary
    daily_summary = {day: {"logs": [], "total_hours": Decimal('0.00')} for day in weekdays}
    calculated_total_hours = Decimal('0.00')

    for log in logs:
        log_day_index = (log.time_in.date() - start_of_week).days
        if 0 <= log_day_index < 7:
            day_name = weekdays[log_day_index]
            local_in = localtime(log.time_in)
            local_out = localtime(log.time_out)

            # Calculate hours as Decimal with 2 decimal places
            hours = Decimal((local_out - local_in).total_seconds() / 3600).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            daily_summary[day_name]["logs"].append({
                "task": log.work_type_names,
                "time_in": local_in.strftime("%I:%M %p"),
                "time_out": local_out.strftime("%I:%M %p"),
            })

            # Update daily and total hours
            daily_summary[day_name]["total_hours"] = (daily_summary[day_name]["total_hours"] + hours).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            calculated_total_hours += hours

    # Get or create payroll
    payroll, created = WeeklyPayroll.objects.get_or_create(
        user=user,
        week_start=start_of_week,
        defaults={
            "rate": Decimal('0.00'),
            "total_hours": calculated_total_hours,
            "total_pay": Decimal('0.00')
        }
    )

    # Update payroll if POST
    if request.method == "POST":
        try:
            rate = Decimal(request.POST.get("rate", "0"))
            payroll.rate = rate
            payroll.total_hours = calculated_total_hours
            payroll.total_pay = (calculated_total_hours * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            payroll.save()
        except (ValueError, InvalidOperation):
            pass

    # Always use payroll record for display
    total_hours = payroll.total_hours.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_pay = payroll.total_pay.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    rate = payroll.rate

    context = {
        "selected_user": user,
        "start_of_week": start_of_week,
        "end_of_week": end_of_week,
        "daily_summary": daily_summary,
        "weekdays": weekdays,
        "total_hours": total_hours,
        "rate": rate,
        "total_pay": total_pay,
    }

    return render(request, "admin_account/user_weekly_summary.html", context)