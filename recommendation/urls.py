from django.urls import path
from . import views
#from .views import test_matrix

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('search-page/', views.search_page, name='search_page'),

    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # لاحظ: لازم destination هنا
    path("favorite/add/<str:destination>/", views.add_favorite, name="add_favorite"),

    path("favorites/", views.favorites_page, name="favorites"),
    path('result/<int:place_id>/', views.place_detail, name='place_detail'),
    path("profile/", views.profile_view, name="profile"),
    path("favorite/remove/<int:place_id>/", views.remove_favorite, name="remove_favorite"), 
    path("place/<int:place_id>/", views.place_detail, name="place_detail"),


    #path("test-matrix/", test_matrix, name="test_matrix"),

]
