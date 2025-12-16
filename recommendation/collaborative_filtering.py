import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from recommendation.models import UserRating, Place

# =============== 1) بناء مصفوفة المستخدم × المكان ===============
def build_user_item_matrix():
    ratings = UserRating.objects.all().values("user_id", "place_id", "rating")
    df = pd.DataFrame(ratings)

    if df.empty:
        return None

    matrix = df.pivot_table(
        index="user_id",
        columns="place_id",
        values="rating"
    )

    return matrix


# =============== 2) بناء مصفوفة التشابه بين المستخدمين ===============
def build_user_similarity_matrix(user_item_matrix):
    matrix_filled = user_item_matrix.fillna(0)
    user_similarity = cosine_similarity(matrix_filled)

    return pd.DataFrame(
        user_similarity,
        index=matrix_filled.index,
        columns=matrix_filled.index
    )


# =============== 3) التوصية للمستخدم ===============
def recommend_for_user(user_id, top_n=5):
    user_item_matrix = build_user_item_matrix()

    if user_item_matrix is None:
        return []

    user_similarity = build_user_similarity_matrix(user_item_matrix)

    # إذا المستخدم ما عندو تقييمات
    if user_id not in user_similarity.index:
        return []

    # ترتيب المستخدمين حسب التشابه
    similar_users = user_similarity[user_id].sort_values(ascending=False)

    # شيل المستخدم نفسه
    similar_users = similar_users.drop(user_id)

    # أعلى 3 مستخدمين مشابهين
    top_similar = similar_users.head(3)

    # أماكن قيموها المستخدمين المشابهين
    user_rated_places = set(
        UserRating.objects.filter(user_id=user_id).values_list('place_id', flat=True)
    )

    recommended_scores = {}

    for other_user_id, sim_score in top_similar.items():
        ratings = UserRating.objects.filter(user_id=other_user_id)

        for r in ratings:
            if r.place_id in user_rated_places:
                continue

            if r.place_id not in recommended_scores:
                recommended_scores[r.place_id] = 0

            recommended_scores[r.place_id] += sim_score * r.rating

    # ترتيب النتائج
    sorted_places = sorted(recommended_scores.items(), key=lambda x: x[1], reverse=True)

    # إرجاع الأماكن فقط
    place_ids = [pid for pid, score in sorted_places[:top_n]]

    return Place.objects.filter(id__in=place_ids)
