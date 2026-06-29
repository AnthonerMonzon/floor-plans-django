from django.urls import path

from core import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard_view, name="dashboard"),
    path("projects/", views.project_list_view, name="project_list"),
    path("projects/new/", views.project_create_view, name="project_create"),
    path("projects/<uuid:project_id>/", views.project_detail_view, name="project_detail"),
    path("projects/<uuid:project_id>/edit/", views.project_edit_view, name="project_edit"),
    path("projects/<uuid:project_id>/floorplans/upload/", views.floorplan_upload_view, name="floorplan_upload"),
    path("projects/<uuid:project_id>/floorplans/<uuid:floorplan_id>/", views.floorplan_viewer_view, name="floorplan_viewer"),
    path("projects/<uuid:project_id>/floorplans/<uuid:floorplan_id>/edit/", views.floorplan_editor_view, name="floorplan_editor"),
    path("projects/<uuid:project_id>/floorplans/<uuid:floorplan_id>/save-crop/", views.floorplan_save_crop_view, name="floorplan_save_crop"),
    path("projects/<uuid:project_id>/floorplans/<uuid:floorplan_id>/delete/", views.floorplan_delete_view, name="floorplan_delete"),
    path("users/", views.user_list_view, name="user_list"),
    path("users/new/", views.user_create_view, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit_view, name="user_edit"),
]
