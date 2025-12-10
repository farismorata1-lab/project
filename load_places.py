import os
import django
import pandas as pd

# --------- 1) إعداد Django ------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proj.settings")
django.setup()

from recommendation.models import Place

# --------- 2) تحميل ملف CSV ------------
csv_path = "enhanced_places_dataset_translated.csv"
df = pd.read_csv(csv_path)

# --------- 3) حذف الأماكن القديمة (اختياري) ------------
# Place.objects.all().delete()

# --------- 4) تجهيز الإدخالات Bulk Insert ------------
places = []

for _, row in df.iterrows():
    place = Place(
        name=row.get("name", ""),
        city=row.get("city", ""),
        country=row.get("country", ""),
        continent=row.get("continent", ""),
        category=row.get("category", ""),
        rating=row.get("rating", 0.0),

        interests=row.get("interests", ""),
        best_visit_season=row.get("best_visit_season", ""),
        budget_range=row.get("budget_range", ""),
        family_friendly=row.get("family_friendly", ""),
        features=row.get("features", ""),

        image_url=row.get("image_url", ""),

        latitude=row.get("latitude", None),
        longitude=row.get("longitude", None),

        semantic_description=row.get("semantic_description", ""),
        semantic_description_ar=row.get("semantic_description_ar", ""),
    )
    places.append(place)

# --------- 5) إدخال البيانات مرة واحدة ------------
Place.objects.bulk_create(places)

print(f"تمت إضافة {len(places)} مكان بنجاح ✔️")
