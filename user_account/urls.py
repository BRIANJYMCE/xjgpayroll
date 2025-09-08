from django.urls import path
from . import views

urlpatterns = [
    path("menu/", views.menu, name="user_menu"),
    path("profile/", views.user_profile, name="user_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("logs/", views.timelog_list, name="timelog_list"),
    path("logs/new/", views.timelog_create, name="timelog_create"),
    path("logs/timein/<int:task_id>/<int:worktype_id>/", views.timelog_timein, name="timelog_timein"),
    path("logs/timeout/<int:timelog_id>/", views.timelog_timeout, name="timelog_timeout"),
    
]
