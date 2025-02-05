# serializers.py
from rest_framework import serializers
from .models import User, Participant

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class ParticipantRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['username', 'email', 'phone_number', 'designation', 'user_image']
        
    def validate_phone_number(self, value):
        if len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        if Participant.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already registered.")
        return value

    def validate_email(self, value):
        if Participant.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

class ParticipantSerializer(serializers.ModelSerializer):
    user_image_url = serializers.SerializerMethodField()
    verified_by = serializers.SerializerMethodField()
    registered_by = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            'id', 'username', 'email', 'phone_number', 'designation',
            'user_image_url', 'qr_verified', 'verified_by', 'verified_at',
            'registered_by', 'created_at'
        ]

    def get_user_image_url(self, obj):
        if obj.user_image:
            return obj.user_image.url
        return None

    def get_verified_by(self, obj):
        if obj.verified_by:
            return obj.verified_by.username
        return None

    def get_registered_by(self, obj):
        if obj.registered_by:
            return obj.registered_by.username
        return None
