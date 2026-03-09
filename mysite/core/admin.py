from django.contrib import admin
from .models import AIRequestLog, APIToken, NetworkLab, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ("title", "is_done", "created_at")
	list_filter = ("is_done", "created_at")
	search_fields = ("title", "description")


@admin.register(NetworkLab)
class NetworkLabAdmin(admin.ModelAdmin):
	list_display = ("name", "owner", "difficulty", "protocols", "routers", "switches", "pcs", "created_at")
	list_filter = ("difficulty", "created_at")
	search_fields = ("name", "protocols", "ip_scheme")


@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
	list_display = ("owner", "model_name", "provider", "cache_hit", "response_ms", "created_at")
	list_filter = ("provider", "model_name", "cache_hit", "created_at")
	search_fields = ("owner__username", "prompt_hash", "prompt_text")


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
	list_display = ("owner", "name", "is_active", "created_at")
	list_filter = ("is_active", "created_at")
	search_fields = ("owner__username", "name", "key")
