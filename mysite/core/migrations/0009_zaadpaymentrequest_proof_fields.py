from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_zaadpaymentrequest_payment_channel_and_receiver"),
    ]

    operations = [
        migrations.AddField(
            model_name="zaadpaymentrequest",
            name="proof_file",
            field=models.FileField(blank=True, upload_to="payment_proofs/"),
        ),
        migrations.AddField(
            model_name="zaadpaymentrequest",
            name="proof_link",
            field=models.URLField(blank=True),
        ),
    ]
