from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from .models import AIRequestLog, APIToken, NetworkLab


User = get_user_model()


class NetworkLabFlowTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="tester", password="secret123")
		self.client.force_login(self.user)

	def test_home_requires_login_when_anonymous(self):
		self.client.logout()
		response = self.client.get(reverse("home"))
		self.assertEqual(response.status_code, 302)
		self.assertIn("/accounts/login/", response.url)

	def test_login_and_logout_flow(self):
		self.client.logout()
		login_page = self.client.get(reverse("login"))
		self.assertEqual(login_page.status_code, 200)

		login_response = self.client.post(
			reverse("login"),
			{"username": "tester", "password": "secret123"},
		)
		self.assertEqual(login_response.status_code, 302)
		self.assertEqual(login_response.url, "/")

		home_response = self.client.get(reverse("home"))
		self.assertEqual(home_response.status_code, 200)

		logout_response = self.client.post(reverse("logout"))
		self.assertEqual(logout_response.status_code, 302)
		self.assertIn("/accounts/login/", logout_response.url)

		after_logout = self.client.get(reverse("home"))
		self.assertEqual(after_logout.status_code, 302)
		self.assertIn("/accounts/login/", after_logout.url)

	def test_anonymous_user_cannot_access_protected_pages(self):
		self.client.logout()

		protected_web_routes = [
			reverse("home"),
			reverse("lab_list"),
			reverse("error_analyzer"),
			reverse("topology_builder"),
			reverse("ai_assistant"),
		]

		for route in protected_web_routes:
			response = self.client.get(route)
			self.assertEqual(response.status_code, 302)
			self.assertIn("/accounts/login/", response.url)

		api_response = self.client.get(reverse("api_labs"))
		self.assertEqual(api_response.status_code, 401)

	def test_home_get(self):
		response = self.client.get(reverse("home"))
		self.assertEqual(response.status_code, 200)

	def test_generate_lab_and_download(self):
		payload = {
			"name": "Auto Test Lab",
			"routers": "2",
			"switches": "2",
			"pcs": "4",
			"vlan_count": "3",
			"ip_scheme": "192.168.0.0/16",
			"difficulty": "beginner",
			"protocols": ["OSPF", "VLAN"],
		}
		response = self.client.post(reverse("home"), payload)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Mermaid Topology")
		self.assertTrue(NetworkLab.objects.filter(name="Auto Test Lab", owner=self.user).exists())

		lab = NetworkLab.objects.get(name="Auto Test Lab", owner=self.user)
		txt_response = self.client.get(reverse("download_lab", args=[lab.id, "txt"]))
		json_response = self.client.get(reverse("download_lab", args=[lab.id, "json"]))
		pdf_response = self.client.get(reverse("download_lab", args=[lab.id, "pdf"]))

		self.assertEqual(txt_response.status_code, 200)
		self.assertEqual(json_response.status_code, 200)
		self.assertEqual(pdf_response.status_code, 200)

	def test_error_analyzer(self):
		get_response = self.client.get(reverse("error_analyzer"))
		self.assertEqual(get_response.status_code, 200)

		post_response = self.client.post(
			reverse("error_analyzer"),
			{"error_output": "% Invalid input detected at '^' marker."},
		)
		self.assertEqual(post_response.status_code, 200)
		self.assertContains(post_response, "CLI syntax error detected")

		config_response = self.client.post(
			reverse("error_analyzer"),
			{"config_output": "router ospf 1\ninterface g0/0\nip address 192.168.1.1 255.255.255.0"},
		)
		self.assertEqual(config_response.status_code, 200)
		self.assertContains(config_response, "OSPF process found but no network statements detected")

	def test_topology_builder_page(self):
		response = self.client.get(reverse("topology_builder"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Interactive Topology Builder")
		self.assertContains(response, "Import JSON")
		self.assertContains(response, "Copy JSON")
		self.assertContains(response, "Download JSON")
		self.assertContains(response, "Link Mode")
		self.assertContains(response, "Snap to Grid")
		self.assertContains(response, "Auto Arrange")
		self.assertContains(response, "Auto Connect")
		self.assertContains(response, "Generate CLI")
		self.assertContains(response, "Copy CLI")
		self.assertContains(response, "Download CLI")
		self.assertContains(response, "Analyze CLI")
		self.assertContains(response, "Paste imported CLI")
		self.assertContains(response, "Severity Filter")
		self.assertContains(response, "Severity:")
		self.assertContains(response, "HIGH: 0 | MEDIUM: 0 | LOW: 0")
		self.assertContains(response, "Remove Selected Link")
		self.assertContains(response, "Edit Last Link Label")
		self.assertContains(response, "Delete/Backspace")
		self.assertContains(response, "Double-click a node")
		self.assertContains(response, "Undo")
		self.assertContains(response, "Redo")

	def test_ai_assistant_page(self):
		response = self.client.get(reverse("ai_assistant"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "AI Lab Assistant")

	def test_ai_assistant_post_without_api_key_creates_log(self):
		response = self.client.post(reverse("ai_assistant"), {"prompt": "Build OSPF lab"})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "OPENAI_API_KEY not set")
		self.assertContains(response, "Recent AI Requests")
		self.assertTrue(AIRequestLog.objects.filter(owner=self.user).exists())

	def test_admin_dashboard_access_rules(self):
		non_admin_response = self.client.get(reverse("admin_dashboard"))
		self.assertEqual(non_admin_response.status_code, 302)

		self.user.is_staff = True
		self.user.save(update_fields=["is_staff"])
		admin_response = self.client.get(reverse("admin_dashboard"))
		self.assertEqual(admin_response.status_code, 200)
		self.assertContains(admin_response, "Activity (Last 7 Days)")
		self.assertContains(admin_response, "Protocol Usage")

	def test_api_requires_session_or_token(self):
		self.client.logout()
		response = self.client.get(reverse("api_labs"))
		self.assertEqual(response.status_code, 401)

	def test_api_token_auth_and_crud(self):
		token = APIToken.objects.create(owner=self.user, name="ci")
		headers = {"HTTP_AUTHORIZATION": f"Token {token.key}"}

		payload = {
			"name": "Token API Lab",
			"routers": 2,
			"switches": 2,
			"pcs": 4,
			"vlan_count": 2,
			"ip_scheme": "10.0.0.0/8",
			"difficulty": "beginner",
			"protocols": ["OSPF", "VLAN"],
		}

		post_response = self.client.post(
			reverse("api_labs"),
			data=json.dumps(payload),
			content_type="application/json",
			**headers,
		)
		self.assertEqual(post_response.status_code, 201)
		lab_id = post_response.json()["id"]

		detail_response = self.client.get(reverse("api_lab_detail", args=[lab_id]), **headers)
		self.assertEqual(detail_response.status_code, 200)
		self.assertEqual(detail_response.json()["name"], "Token API Lab")

		delete_response = self.client.delete(reverse("api_lab_detail", args=[lab_id]), **headers)
		self.assertEqual(delete_response.status_code, 200)
		self.assertFalse(NetworkLab.objects.filter(id=lab_id).exists())
