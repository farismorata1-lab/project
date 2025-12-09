import requests
import re

# مفاتيح الـ APIs
UNSPLASH_ACCESS_KEY = "sUJK0xo0kcFiRxj1I4CBtn3Q7KngvkFBv2AcTRQ_-QM"
WEATHER_API_KEY = "b0bfefbbffcc096e5f493b2b95843cc1"

# كاش بسيط لتسريع الصور
image_cache = {}

def get_image_url(destination):
    """جلب صورة من Unsplash حسب الوجهة"""
    if destination in image_cache:
        return image_cache[destination]

    headers = {
        "Accept-Version": "v1",
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    params = {
        "query": destination,
        "per_page": 1,
        "orientation": "landscape"
    }

    try:
        response = requests.get("https://api.unsplash.com/search/photos", headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            image_url = data["results"][0]["urls"].get("regular")
            if image_url:
                image_cache[destination] = image_url
                return image_url
    except requests.RequestException as e:
        print(f"[UNSPLASH ERROR] {e}")

    fallback = "/static/images/fallback.jpg"
    image_cache[destination] = fallback
    return fallback


def get_weather(city_name):
    """جلب حالة الطقس من OpenWeatherMap"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&units=metric&lang=ar"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "city": city_name,
            "description": data["weather"][0]["description"],
            "icon": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
            "temperature": round(data["main"]["temp"]),
            "main": data["weather"][0]["main"]
        }
    except Exception as e:
        print(f"[WEATHER ERROR] {e}")
        return None
    

# -----------------------------
# استخراج الدولة من نص البحث
# -----------------------------
def extract_country_from_input(text):
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

    # لغة عربية
    for ar, en in countries_ar.items():
        if ar in text:
            return ar, en

    # لغة إنجليزية
    for key, value in countries_en.items():
        if key in text:
            return None, value

    return None, None


def normalize_arabic(text):
    if not text:
        return ""

    # إزالة التشكيل
    text = re.sub(r'[\u064B-\u0652]', '', text)

    # توحيد الألف
    text = re.sub(r'[إأآا]', 'ا', text)

    # توحيد الياء
    text = re.sub(r'[يى]', 'ي', text)

    # إزالة الهمزة المتطرفة
    text = text.replace("ؤ", "و").replace("ئ", "ي")

    # إزالة التنوين
    text = text.replace("ًا", "ا").replace("اً", "ا")

    return text.strip()

def arabic_query_expand(text):
    base = normalize_arabic(text)

    synonyms = {
        "اهرامات": "اهرامات الجيزة مصر القاهرة",
        "البتراء": "البتراء البتراء الاردن معلم اثري",
        "المسجد": "مسجد اسلامي جامع",
        "قلعة": "قلعة حصن تاريخ اثر",
        "شاطئ": "شاطئ بحر شواطئ ساحل"
    }

    expanded = base
    for key, extra in synonyms.items():
        if key in base:
            expanded += " " + extra

    return expanded
