from django.urls import path
from .views import ShortenURL, RedirectURL, URLStats

urlpatterns = [
    path('shorten/', ShortenURL.as_view(), name='shorten'),
    path('<str:short_code>/', RedirectURL.as_view(), name='redirect'),
    path('<str:short_code>/stats/', URLStats.as_view(), name='stats'),
]
    