from django.urls import path
from .views import (
    admin_dashboard,
    ai_assistant,
    activate_account,
    api_health,
    api_create_token,
    api_lab_detail,
    api_labs,
    download_lab,
    error_analyzer,
    home,
    lab_list,
    signup,
    topology_builder,
)

urlpatterns = [
    path("accounts/signup/", signup, name="signup"),
    path("accounts/activate/<uidb64>/<token>/", activate_account, name="activate_account"),
    path("", home, name="home"),
    path("labs/", lab_list, name="lab_list"),
    path("labs/<int:lab_id>/download/<str:filetype>/", download_lab, name="download_lab"),
    path("analyzer/", error_analyzer, name="error_analyzer"),
    path("topology-builder/", topology_builder, name="topology_builder"),
    path("ai-assistant/", ai_assistant, name="ai_assistant"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),

    path("api/health/", api_health, name="api_health"),
    path("api/tokens/create/", api_create_token, name="api_create_token"),
    path("api/labs/", api_labs, name="api_labs"),
    path("api/labs/<int:lab_id>/", api_lab_detail, name="api_lab_detail"),
]
