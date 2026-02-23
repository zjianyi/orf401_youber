from django.db import migrations
import random
import string
from datetime import timedelta
from django.utils import timezone


def generate_code(existing_codes, length=8):
    """
    Helper used inside the migration to generate a short unique event code.
    """
    alphabet = string.ascii_uppercase + string.digits
    code = "".join(random.choice(alphabet) for _ in range(length))
    while code in existing_codes:
        code = "".join(random.choice(alphabet) for _ in range(length))
    existing_codes.add(code)
    return code


def seed_events(apps, schema_editor):
    Event = apps.get_model("rides", "Event")

    existing_codes = set(Event.objects.values_list("code", flat=True))
    now = timezone.now()

    examples = [
        {
            "name": "Nets vs Celtics",
            "destination_name": "Barclays Center",
            "destination_address": "620 Atlantic Ave, Brooklyn, NY",
            "city": "New York",
            "category": "sports",
        },
        {
            "name": "Kendrick Lamar Live",
            "destination_name": "Wells Fargo Center",
            "destination_address": "3601 S Broad St, Philadelphia, PA",
            "city": "Philadelphia",
            "category": "sports",
        },
        {
            "name": "Global Climate Conference (COP-style)",
            "destination_name": "Convention Center",
            "destination_address": "123 Conference Way",
            "city": "Glasgow",
            "category": "professional",
        },
    ]

    for idx, data in enumerate(examples):
        # Avoid creating duplicates if this migration is re-run.
        if Event.objects.filter(
            name=data["name"],
            destination_name=data["destination_name"],
            city=data["city"],
        ).exists():
            continue

        start = now + timedelta(days=7 + idx)
        end = start + timedelta(hours=4)

        code = generate_code(existing_codes)

        Event.objects.create(
            name=data["name"],
            destination_name=data["destination_name"],
            destination_address=data["destination_address"],
            city=data["city"],
            category=data["category"],
            is_public=True,
            start_time=start,
            end_time=end,
            code=code,
        )


def unseed_events(apps, schema_editor):
    Event = apps.get_model("rides", "Event")
    names = [
        "Nets vs Celtics",
        "Kendrick Lamar Live",
        "Global Climate Conference (COP-style)",
    ]
    Event.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("rides", "0003_auto_20260223_1835"),
    ]

    operations = [
        migrations.RunPython(seed_events, unseed_events),
    ]

