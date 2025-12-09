from django.db import models
from django.contrib.auth.models import User


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.destination}"


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=255)
    rating = models.IntegerField(default=0)  # 1 → 5
    rated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.destination} → {self.rating}⭐"


class Place(models.Model):
    # البيانات الأساسية
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    continent = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=255, blank=True)
    rating = models.FloatField(default=0)

    # وصف ومعلومات إضافية
    interests = models.CharField(max_length=500, blank=True)
    best_visit_season = models.CharField(max_length=255, blank=True)
    budget_range = models.CharField(max_length=100, blank=True)
    family_friendly = models.CharField(max_length=10, blank=True)
    features = models.CharField(max_length=500, blank=True)

    # صورة
    image_url = models.URLField(blank=True)

    # إحداثيات
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # التضمينات الدلالية
    semantic_description = models.TextField(blank=True)
    semantic_description_ar = models.TextField(blank=True)

    def __str__(self):
        return self.name
