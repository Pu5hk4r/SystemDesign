from rest_framework import serializers
from .models import URL

class URLCreateSerializer(serializers.ModelSerializer):
    custom_code = serializers.CharField(required = False, allow_blank = True)
    short_code = serializers.CharField(read_only = True)

    class Meta:
        model = URL
        fields = ['original_url', 'custom_code', 'short_code']



class URLResponseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = URL
        fields = ['id', 'original_url', 'short_code','clicks','is_active', 'created_at']