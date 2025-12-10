# recommendation/views.py
import os
import pickle
import faiss
import requests
import numpy as np
from django.shortcuts import render
from django.conf import settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
from functools import lru_cache
from sklearn.metrics.pairwise import cosine_similarity
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Favorite, UserRating, Place
from .forms import RegisterForm
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from .models import Place
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .models import Favorite, Place
from django.http import HttpResponse
from recommendation.collaborative_filtering import build_user_item_matrix
from .collaborative_filtering import build_user_item_matrix, recommend_for_user



# دوال utils (تأكد إن utils.py يحتوي على: get_image_url, get_weather, extract_country_from_input)
from .utils import get_image_url, get_weather, extract_country_from_input ,arabic_query_expand

# ----------------------------
# مسارات قوية
# ----------------------------
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

INDEX_AR_PATH = BASE_DIR / "tourism_index_ar.faiss"
INDEX_EN_PATH = BASE_DIR / "tourism_index_en.faiss"
DATA_AR_PATH  = BASE_DIR / "tourism_data_ar.pkl"
DATA_EN_PATH  = BASE_DIR / "tourism_data_en.pkl"
EMB_AR_PATH   = BASE_DIR / "embeddings_ar.npy"
EMB_EN_PATH   = BASE_DIR / "embeddings_en.npy"

# ----------------------------
# تحميل النماذج (مرة واحدة عند استيراد الملف)
# ----------------------------
model_ar = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
model_en = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# ----------------------------
# تحقق من وجود الملفات المطلوبة
# ----------------------------
missing = []
for p in (INDEX_AR_PATH, INDEX_EN_PATH, DATA_AR_PATH, DATA_EN_PATH, EMB_AR_PATH, EMB_EN_PATH):
    if not p.exists():
        missing.append(str(p))
if missing:
    raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))

# ----------------------------
# تحميل FAISS + البيانات + التضمينات
# ----------------------------
index_ar = faiss.read_index(str(INDEX_AR_PATH))
index_en = faiss.read_index(str(INDEX_EN_PATH))

with open(DATA_AR_PATH, "rb") as f:
    data_ar = pickle.load(f)   # list of dicts (records)
with open(DATA_EN_PATH, "rb") as f:
    data_en = pickle.load(f)

# تحميل مصفوفات التضمينات الحقيقية (aligns with data_xxx)
emb_ar = np.load(str(EMB_AR_PATH)).astype("float32")
emb_en = np.load(str(EMB_EN_PATH)).astype("float32")

# ----------------------------
# كشف اللغة — نسخة محسنة
# ----------------------------
def is_arabic_text(text: str) -> bool:
    if not text:
        return False
    for ch in text:
        if "\u0600" <= ch <= "\u06FF":
            return True
    return False

# ----------------------------
# صفحتين ثابتتين
# ----------------------------
def home(request):
    return render(request, "recommendation/index.html")


def search_page(request):
    return render(request, "recommendation/search.html")


# ----------------------------
# دالة البحث (نسخة احترافية — تتبع منطق Flask)
# ----------------------------
def search(request):
    query = request.GET.get("query", "").strip()

    if not query:
        return render(request, "recommendation/results.html", {"message": "يرجى كتابة كلمة للبحث"})

    # تحديد اللغة
    is_ar = is_arabic_text(query)

    # اختيار المصادر الصحيحة
    if is_ar:
        processed_query = arabic_query_expand(query)
        embedding = model_ar.encode([processed_query], convert_to_numpy=True).astype("float32")

        index = index_ar
        data = data_ar
        emb_matrix = emb_ar
    else:
        embedding = model_en.encode([query], convert_to_numpy=True).astype("float32")
        index = index_en
        data = data_en
        emb_matrix = emb_en

    # normalize كما في Flask
    faiss.normalize_L2(embedding)

    # بحث أولي عميق (initial_k = 200)
    initial_k = 200
    k = min(initial_k, max(1, index.ntotal))
    D, I = index.search(embedding, k)

    # استخراج مؤشرات المرشحين
    candidate_idxs = I[0].tolist()
    candidate_embeds = emb_matrix[candidate_idxs]

    # حساب cosine similarity
    cosine_scores = cosine_similarity(embedding, candidate_embeds)[0]

    # استخراج الدولة من نص البحث
    ar_country, en_country = extract_country_from_input(query)

    results = []
    similarity_threshold = 0.30

    activity_synonyms = {
        "historical": ["historical", "history", "تاريخ", "تاريخي"],
        "nature": ["nature", "natural", "طبيعة"],
        "adventure": ["adventure", "مغامرة"],
        "museum": ["museum", "cultural", "ثقافي", "متحف"],
        "shopping": ["shopping", "market", "تسوق"],
        "sport": ["sport", "sports", "رياضي", "رياضة", "ملعب"]
    }

    for i, idx in enumerate(candidate_idxs):
        sim = float(cosine_scores[i])
        if sim < similarity_threshold:
            continue

        item = data[idx]
        row_country = str(item.get("country") or item.get("Country") or "").lower()
        row_category = str(item.get("category") or item.get("Category") or "").lower()

        # فلترة الدولة
        if ar_country or en_country:
            country_ok = False
            for c in [ar_country, en_country]:
                if c and c.lower() in row_country:
                    country_ok = True
                    break
            if not country_ok:
                continue

        # فلترة النشاط
        activity_filter = request.GET.get("activity", "").strip().lower()
        if activity_filter and activity_filter != "any":
            possible_synonyms = activity_synonyms.get(activity_filter, [activity_filter])
            matched_activity = False

            for syn in possible_synonyms:
                if syn in row_category:
                    matched_activity = True
                    break

            if not matched_activity:
                if any(word in query.lower() for word in possible_synonyms):
                    matched_activity = True

            if not matched_activity:
                continue

        # استخراج البيانات
        name = item.get("destination") or item.get("Destination") or item.get("name") or item.get("Name") or ""
        city = item.get("city") or item.get("City") or item.get("CityName") or ""
        country = item.get("country") or item.get("Country") or ""
        category = item.get("category") or item.get("Category") or ""
        rating = item.get("rating") or item.get("Rating") or 0.0
        description = (item.get("semantic_description_ar") if is_ar else item.get("semantic_description")) or ""

        # ✨ إضافة ربط النتيجة بقاعدة البيانات
        place = Place.objects.filter(name__iexact=name).first()
        place_id = place.id if place else None

        # إضافة النتيجة للواجهة
        results.append({
            "name": name,
            "city": city,
            "country": country,
            "category": category,
            "rating": rating,
            "description": description,
            "score": sim,
            "place_id": place_id
        })

    if not results:
        return render(request, "recommendation/results.html", {"message": "لا توجد نتائج مطابقة"})

    # ترتيب نهائي
    results.sort(key=lambda x: x["score"], reverse=True)

    # إضافة الصور والطقس
    for item in results:
        img_query = f"{item['name']} {item['city']} {item['country']}".strip()
        item["image_url"] = get_image_url(img_query)
        item["weather"] = get_weather(item["city"])

    return render(request, "recommendation/results.html", {"results": results})



def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            return redirect("login")   # ✔ أفضل من render
    else:
        form = RegisterForm()

    return render(request, "recommendation/signup.html", {"form": form})


from django.contrib.auth.models import User

def login_view(request):
    error = None

    if request.method == "POST":
        input_value = request.POST.get("username")
        password = request.POST.get("password")

        username = input_value  # مبدئياً

        # لو كتب إيميل — نمشي نجيبه
        if "@" in input_value:
            try:
                user_obj = User.objects.get(email=input_value)
                username = user_obj.username
            except User.DoesNotExist:
                pass  # خليه يحاول باليوزر العادي

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            error = "البيانات غير صحيحة"

    return render(request, "recommendation/login.html", {"error": error})

def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def add_favorite(request, destination):
    if request.method == "POST":
        Favorite.objects.create(
            user=request.user,
            destination=destination
        )
        return redirect("favorites")   # ✔ يرجع لصفحة المفضلة

    return redirect("home")


def place_detail(request, place_id):
    place = Place.objects.filter(id=place_id).first()

    if not place:
        return render(request, "recommendation/place_detail.html", {
            "message": "المكان غير موجود"
        })

    # صور إضافية (من العمود extra_images) لو موجودة
    extra_images = []
    if place.extra_images:
        extra_images = place.extra_images.split(",")  # لو مخزنة كسلسلة

    # أماكن مشابهة (حسب التصنيف)
    similar_places = Place.objects.filter(category=place.category).exclude(id=place_id)[:4]

    return render(request, "recommendation/place_detail.html", {
        "place": place,
        "similar": similar_places,
        "extra_images": extra_images
    })


def profile_view(request):
    user = request.user  # المستخدم الحالي

    # حساب عدد المفضلات
    favorites = Favorite.objects.filter(user=user).select_related("place")

    context = {
        "username": user.username,
        "email": user.email,
        "favorites": favorites,
    }
    return render(request, "recommendation/profile.html", context)



def add_favorite(request, destination):
    if not request.user.is_authenticated:
        messages.error(request, "يجب تسجيل الدخول أولاً")
        return redirect("login")

    place = get_object_or_404(Place, Destination=destination)

    # تحقق إذا كانت موجودة مسبقاً
    already_exists = Favorite.objects.filter(user=request.user, place=place).exists()

    if already_exists:
        messages.warning(request, "هذا المكان موجود بالفعل في المفضلة")
    else:
        Favorite.objects.create(user=request.user, place=place)
        messages.success(request, "تمت إضافة المكان إلى المفضلة بنجاح!")

    # العودة لنفس صفحة التفاصيل
    return redirect("place_detail", place_id=place.id)

def remove_favorite(request, place_id):
    if not request.user.is_authenticated:
        return redirect("login")

    Favorite.objects.filter(user=request.user, place_id=place_id).delete()

    return redirect("profile")

def test_collab_matrix(request):
    matrix = build_user_item_matrix()
    print("User-Item Matrix:")
    print(matrix)
    return HttpResponse("Matrix printed in terminal!")

def test_collab_recommend(request, user_id):
    results = recommend_for_user(user_id)
    print(f"Recommendations for user {user_id}:")
    for p in results:
        print(p.name)
    return HttpResponse(f"Done! Check terminal for results of user {user_id}.")


@login_required
def favorites_page(request):
    favs = Favorite.objects.filter(user=request.user).order_by("-added_at")
    return render(request, "recommendation/favorites.html", {"favorites": favs})
