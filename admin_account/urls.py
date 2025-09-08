from django.urls import path
from admin_account import views

urlpatterns = [
    path("menu/", views.admin_main_menu, name="admin_main_menu"),
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/assign/", views.assign_task, name="assign_task"),
    path('tasks/stop/<int:log_id>/', views.stop_shift, name='stop_shift'),
    path('tasks/delete/<int:log_id>/', views.delete_shift, name='delete_shift'),

    path('options/', views.worktype_options, name='worktype_options'),
    path('options/edit/<int:pk>/', views.worktype_edit, name='worktype_edit'),
    path('options/delete/<int:pk>/', views.worktype_delete, name='worktype_delete'),
    path("worktype/<int:pk>/delete/", views.worktype_delete, name="worktype_delete"),
    path("manage-users/", views.manage_users, name="manage_users"),
    path('manage-users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    
    path(
    "admin_account/user-weekly-summary/<int:user_id>/<str:week_start>/",
    views.user_weekly_summary,
    name="user_weekly_summary"
    ),
    
    path("user-week-list/<int:user_id>/", views.user_week_list, name="user_week_list"),


]
