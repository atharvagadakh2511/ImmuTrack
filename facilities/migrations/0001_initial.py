from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Facility",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("facility_id", models.CharField(max_length=20, unique=True)),
                ("district", models.CharField(max_length=100)),
                ("city_or_locality", models.CharField(max_length=150)),
                ("facility_name", models.CharField(max_length=255)),
                ("facility_type", models.CharField(max_length=100)),
                ("ownership", models.CharField(choices=[("Government", "Government"), ("Private", "Private")], max_length=50)),
                ("vaccination_service_status", models.CharField(default="Not verified - contact facility", max_length=100)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("full_address", models.TextField(blank=True)),
                ("latitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ("source_url", models.URLField(blank=True)),
                ("data_note", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Hospital / Vaccination Centre",
                "verbose_name_plural": "Hospitals / Vaccination Centres",
                "ordering": ["district", "facility_name"],
            },
        ),
    ]
