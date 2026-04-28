from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, redirect
from .models import URL
from .serializers import URLCreateSerializer,  URLResposneSerializer

class ShortenURL(APIView):
    def post(self, request):
        serializer  = URLCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RedirectURL(APIView):
    def get(self, request, short_code):
        url = get_object_or_404(URL, short_code=short_code, is_active=True)
        url.click_count += 1
        url.save()
        return redirect(url.long_url)

class URLStats(APIView):
    def get(self, request, short_code):
        url = get_object_or_404(URL, short_code=short_code)
        serializer = URLResposneSerializer(url)
        return Response(serializer.data)