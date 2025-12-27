from django.core.management.base import BaseCommand
from django.conf import settings
import csv
import os

from recommendation.models import Place


class Command(BaseCommand):
    help = "Import places from CSV file"

    def handle(self, *args, **kwargs):
        # المسار الصحيح لملف CSV
        file_path = os.path.join(
            settings.BASE_DIR,
            "enhanced_places_dataset_translated.csv"
        )

        # تأكيد وجود الملف
        if not os.path.exists(file_path):
            self.stderr.write(
                self.style.ERROR(f"❌ CSV file not found: {file_path}")
            )
            return

        with open(file_path, encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                Place.objects.update_or_create(
                    name=row["Destination"].strip(),
                    city=row["City"].strip(),
                    country=row["Country"].strip(),
                    defaults={
                        "continent": row["Continent"].strip(),
                        "category": row["Category"].strip(),
                        "rating": float(row["Rating"]) if row["Rating"] else 0.0,
                        "interests": row["Interests"].strip(),
                        "best_visit_season": row["Best_Visit_Season"].strip(),
                        "budget_range": row["Budget_Range"].strip(),
                        "family_friendly": row["Family_Friendly"].strip(),
                        "features": row["Features"].strip(),
                        "latitude": float(row["Latitude"]) if row["Latitude"] else None,
                        "longitude": float(row["Longitude"]) if row["Longitude"] else None,
                        "semantic_description": row["semantic_description"].strip(),
                        "semantic_description_ar": row["semantic_description_ar"].strip(),
                    }
                )

        self.stdout.write(
            self.style.SUCCESS("✅ Places imported successfully")
        )
