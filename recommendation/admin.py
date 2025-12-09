from django.contrib import admin
from .models import Place, Favorite, Rating

admin.site.register(Favorite)
admin.site.register(Rating)
admin.site.register(Place)


