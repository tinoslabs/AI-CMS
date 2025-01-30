from rest_framework import serializers
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    user_image = serializers.ImageField(required=False, allow_null=True) 

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'user_image']

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_phone_number(self, value):
        """Ensure phone number is unique and exactly 10 digits"""
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already registered.")
        return value

    def create(self, validated_data):
        """Create user instance with uploaded image"""
        return User.objects.create(**validated_data)

