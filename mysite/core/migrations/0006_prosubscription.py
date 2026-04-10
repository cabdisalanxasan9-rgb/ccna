from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_apitoken"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan_name", models.CharField(default="pro_monthly", max_length=60)),
                (
                    "status",
                    models.CharField(
                        choices=[("inactive", "Inactive"), ("active", "Active"), ("canceled", "Canceled")],
                        default="inactive",
                        max_length=20,
                    ),
                ),
                ("current_period_end", models.DateTimeField(blank=True, null=True)),
                ("last_payment_at", models.DateTimeField(blank=True, null=True)),
                ("stripe_customer_id", models.CharField(blank=True, max_length=120)),
                ("stripe_subscription_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("stripe_checkout_session_id", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pro_subscription",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
    ]
