import requests
import re
from django.conf import settings
import os
from dotenv import load_dotenv

# ----------------------------------
# كاش بسيط لتسريع الصور
# ----------------------------------
image_cache = {}

# ----------------------------------
# جلب صورة من Unsplash
# ----------------------------------
# def get_image_url(destination):
#     if not destination:
#         return None

#     if destination in image_cache:
#         return image_cache[destination]

#     headers = {
#         "Accept-Version": "v1",
#         "Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}",
#     }

#     params = {
#         "query": destination,
#         "per_page": 1,
#         "orientation": "landscape",
#     }

#     try:
#         response = requests.get(
#             "https://api.unsplash.com/search/photos",
#             headers=headers,
#             params=params,
#             timeout=5,
#         )
#         response.raise_for_status()
#         data = response.json()

#         if data.get("results"):
#             image_url = data["results"][0]["urls"]["regular"]
#             image_cache[destination] = image_url
#             return image_url

#     except requests.RequestException as e:
#         print(f"[UNSPLASH ERROR] {e}")

#     image_cache[destination] = None
#     return None


# ----------------------------------
# جلب حالة الطقس
# ----------------------------------
def get_weather(city_name):
    if not city_name:
        return None

    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={city_name}"
        f"&appid={os.getenv('WEATHER_API_KEY')}"
        f"&units=metric"
        f"&lang=ar"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        return {
            "city": city_name,
            "description": data["weather"][0]["description"],
            "icon": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
            "temperature": round(data["main"]["temp"]),
            "main": data["weather"][0]["main"],
        }

    except Exception as e:
        print(f"[WEATHER ERROR] {e}")
        return None


# ----------------------------------
# استخراج الدولة من نص البحث
# ----------------------------------
def extract_country_from_input(text):
    if not text:
        return None, None

    text = text.lower().strip()

    countries_ar = {
        "السعودية": "saudi arabia",
        "مصر": "egypt",
        "المغرب": "morocco",
        "الجزائر": "algeria",
        "الأردن": "jordan",
        "تونس": "tunisia",
    }

    countries_en = {
        "saudi": "saudi arabia",
        "egypt": "egypt",
        "morocco": "morocco",
        "algeria": "algeria",
        "jordan": "jordan",
        "tunisia": "tunisia",
    }

    for ar, en in countries_ar.items():
        if ar in text:
            return ar, en

    for key, value in countries_en.items():
        if key in text:
            return None, value

    return None, None


# ----------------------------------
# توحيد النص العربي
# ----------------------------------
def normalize_arabic(text):
    if not text:
        return ""

    text = re.sub(r"[\u064B-\u0652]", "", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"[يى]", "ي", text)
    text = text.replace("ؤ", "و").replace("ئ", "ي")
    text = text.replace("ًا", "ا").replace("اً", "ا")

    return text.strip()


# ----------------------------------
# توسيع البحث العربي
# ----------------------------------
def arabic_query_expand(text):
    base = normalize_arabic(text)

    synonyms = {
        "اهرامات": "اهرامات الجيزة مصر القاهرة",
        "البتراء": "البتراء الاردن معلم اثري",
        "المسجد": "مسجد اسلامي جامع",
        "قلعة": "قلعة حصن تاريخي اثر",
        "شاطئ": "شاطئ بحر ساحل",
    }

    expanded = base
    for key, extra in synonyms.items():
        if key in base:
            expanded += " " + extra

    return expanded


# ----------------------------------
# تنظيف أسماء الأماكن
# ----------------------------------
def clean_place_names():
    from recommendation.models import Place

    for place in Place.objects.all():
        original = place.name
        new_name = (
            place.name.strip()
            .replace("ـ", "")
            .replace("  ", " ")
            .replace("'", "")
            .replace("`", "")
            .lower()
            .title()
        )

        if new_name != original:
            place.name = new_name
            place.save()
            print(f"Updated: {original} → {new_name}")
