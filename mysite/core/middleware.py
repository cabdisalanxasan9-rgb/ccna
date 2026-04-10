from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect

from .models import ProSubscription


class ProAccessMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if not getattr(settings, "PRO_FEATURES_REQUIRE_PAYMENT", True):
			return self.get_response(request)

		path = (request.path or "").strip()
		exempt_prefixes = (
			"/ai-assistant/",
			"/billing/pro/",
			"/api/billing/stripe/webhook/",
		)
		if any(path.startswith(prefix) for prefix in exempt_prefixes):
			return self.get_response(request)

		prefixes = getattr(settings, "PRO_ONLY_PATH_PREFIXES", ())
		if not prefixes:
			return self.get_response(request)

		if not any(path.startswith(prefix) for prefix in prefixes):
			return self.get_response(request)

		user = getattr(request, "user", None)
		if not user or not user.is_authenticated:
			if path.startswith("/api/"):
				return JsonResponse({"error": "Authentication required."}, status=401)
			return redirect(settings.LOGIN_URL)

		if user.is_staff:
			return self.get_response(request)

		subscription = ProSubscription.objects.filter(owner=user).first()
		has_active_pro = bool(subscription and subscription.is_active_now)
		if has_active_pro:
			return self.get_response(request)

		if path.startswith("/api/"):
			return JsonResponse(
				{
					"error": "Pro subscription required.",
					"detail": "Upgrade to Pro to access this endpoint.",
				},
				status=402,
			)

		request.session["billing_status_note"] = "Pro access required. Upgrade to continue."
		return redirect("ai_assistant")