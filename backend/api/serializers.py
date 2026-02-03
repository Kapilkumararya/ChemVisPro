from rest_framework import serializers
from django.contrib.auth.models import User
from .models import EquipmentDataset

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # This creates the user and automatically hashes the password
        user = User.objects.create_user(**validated_data)
        return user

class EquipmentDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDataset
        fields = '__all__'