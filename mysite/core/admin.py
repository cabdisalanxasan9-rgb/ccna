from django.contrib import admin
from django.utils import timezone

from .models import AIRequestLog, APIToken, NetworkLab, ProSubscription, Task, ZaadPaymentRequest


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


@admin.register(ProSubscription)
class ProSubscriptionAdmin(admin.ModelAdmin):
	list_display = ("owner", "plan_name", "status", "current_period_end", "updated_at")
	list_filter = ("status", "plan_name", "updated_at")
	search_fields = ("owner__username", "stripe_customer_id", "stripe_subscription_id")


@admin.register(ZaadPaymentRequest)
class ZaadPaymentRequestAdmin(admin.ModelAdmin):
	list_display = ("owner", "reference", "amount", "currency", "status", "created_at", "reviewed_at")
	list_filter = ("status", "currency", "created_at")
	search_fields = ("owner__username", "reference", "sender_phone")
	actions = ("approve_requests", "reject_requests")

	@admin.action(description="Approve selected Zaad requests and activate Pro")
	def approve_requests(self, request, queryset):
		now = timezone.now()
		approved_count = 0
		for payment in queryset.select_related("owner"):
			payment.status = ZaadPaymentRequest.STATUS_APPROVED
			payment.reviewed_by = request.user
			payment.reviewed_at = now
			payment.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

			subscription, _ = ProSubscription.objects.get_or_create(owner=payment.owner)
			subscription.status = ProSubscription.STATUS_ACTIVE
			subscription.plan_name = "pro_zaad_manual"
			subscription.last_payment_at = now
			subscription.save()
			approved_count += 1

		self.message_user(request, f"Approved {approved_count} request(s) and activated Pro.")

	@admin.action(description="Reject selected Zaad requests")
	def reject_requests(self, request, queryset):
		now = timezone.now()
		updated = queryset.update(
			status=ZaadPaymentRequest.STATUS_REJECTED,
			reviewed_by=request.user,
			reviewed_at=now,
		)
		self.message_user(request, f"Rejected {updated} request(s).")
