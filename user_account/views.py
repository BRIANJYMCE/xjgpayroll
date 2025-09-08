from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from .models import TimeLog
from admin_account.models import WorkAssignment
from admin_account.models import WorkType
from django.shortcuts import render
from accounts.models import Profile
from .forms import UserForm, ProfileForm
from django.contrib import messages
from django.core.paginator import Paginator


@login_required
def menu(request):
    """User main menu."""
    return render(request, "user_account/menu.html")


@login_required
def timelog_list(request):
    # Get filter values from GET parameters
    date_filter = request.GET.get("date_filter")
    work_type_filter = request.GET.get("work_type_filter")

    # Base queryset
    logs = TimeLog.objects.filter(user=request.user).select_related("task", "work_type").order_by("-time_in")

    if date_filter:
        try:
            # Ensure string is in YYYY-MM-DD format
            parsed_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            logs = logs.filter(time_in__date=parsed_date)
        except ValueError:
            logs = logs.none()  # or just ignore filter

    # Apply work type filter if provided
    if work_type_filter:
        logs = logs.filter(work_type_names__icontains=work_type_filter)

    # Prepare timelogs for display
    timelogs = []
    all_timelogs_dates = set()
    all_work_types = set()

    for log in logs:
        local_in = timezone.localtime(log.time_in) if log.time_in else None
        local_out = timezone.localtime(log.time_out) if log.time_out else None

        # Track unique dates and work types for filter dropdowns
        if local_in:
            all_timelogs_dates.add(local_in.date())
        if log.work_type_names:
            all_work_types.add(log.work_type_names)
        elif log.work_type:
            all_work_types.add(log.work_type.name)

        # Work types
        work_types = log.work_type_names if log.time_out else (log.work_type.name if log.work_type else "—")

        # Hours calculation
        if local_in and local_out:
            diff = local_out - local_in
            total_hours = f"{round(diff.total_seconds() / 3600, 2)} hrs"
        elif local_in:
            total_hours = "Ongoing"
        else:
            total_hours = "-"

        timelogs.append({
            "id": log.id,
            "date": local_in.date() if local_in else None,
            "completed_date": log.completed_date,
            "time_in": local_in.time() if local_in else None,
            "time_out": local_out.time() if local_out else None,
            "total_hours": total_hours,
            "work_types": work_types,
        })

    # Pagination
    paginator = Paginator(timelogs, 10)  # 10 logs per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "all_timelogs_dates": sorted(all_timelogs_dates, reverse=True),
        "all_work_types": sorted(all_work_types),
        "request": request,  # to preserve filter values in template
    }

    return render(request, "user_account/timelog_list.html", context)
    

@login_required
def timelog_create(request):
    user = request.user

    # 1️⃣ Active logs (time_in without time_out)
    active_logs = TimeLog.objects.filter(
        user=user,
        time_out__isnull=True
    ).select_related("task", "work_type")

    active_worktype_ids = active_logs.values_list("work_type_id", flat=True)

    # 2️⃣ Assigned work items (exclude active ones to avoid redundancy)
    assigned_work_items = []
    tasks = WorkAssignment.objects.filter(user=user)

    for task in tasks:
        for wt in task.work_types.filter(is_active=True).exclude(id__in=active_worktype_ids):
            assigned_work_items.append({
                "task": task,
                "work_type": wt
            })

    return render(request, "user_account/timelog_form.html", {
        "active_logs": active_logs,
        "assigned_work_items": assigned_work_items,
    })


@login_required
def timelog_timein(request, task_id, worktype_id):
    task = get_object_or_404(WorkAssignment, id=task_id, user=request.user)
    work_type = get_object_or_404(WorkType, id=worktype_id)

    # 🚨 Server-side safeguard
    if TimeLog.objects.filter(user=request.user, time_out__isnull=True).exists():
        messages.error(request, "⚠️ You already have an active task. Please finish it first.")
        return redirect("timelog_create")

    # ✅ Safe to create new log
    TimeLog.objects.create(
        user=request.user,
        task=task,
        work_type=work_type,
        work_type_names=work_type.name,
        time_in=timezone.now()
    )
    messages.success(request, f"✅ Time In for {work_type.name}")
    return redirect("timelog_create")



@login_required
def timelog_timeout(request, timelog_id):
    """Time Out for a single work type log."""
    timelog = get_object_or_404(TimeLog, id=timelog_id, user=request.user)
    if timelog.time_out is None:
        timelog.time_out = timezone.now()
        timelog.save()
    return redirect("timelog_list")

@login_required
def user_profile(request):
    # Get the profile linked to the current user
    profile = getattr(request.user, "profile", None)

    return render(
        request,
        "user_account/user_profile.html",  # or "user_account/user_profile.html" depending on where you placed it
        {
            "user": request.user,
            "profile": profile,
        },
    )

@login_required
def edit_profile(request):
    user = request.user
    profile = user.profile  # thanks to OneToOneField

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("user_profile")
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(
        request,
        "user_account/edit_profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )

