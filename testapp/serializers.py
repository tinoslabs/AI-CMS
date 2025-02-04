from rest_framework import serializers
from .models import User

# class UserRegistrationSerializer(serializers.ModelSerializer):
#     # user_image = serializers.ImageField(required=True)  # Make the image field required
#     phone_number = serializers.CharField(required=True, max_length=15)  # Ensure phone number is required

#     class Meta:
#         model = User
#         fields = ['username', 'email', 'phone_number', 'user_image']  # Keep phone_number and user_image in the list

#     def validate_email(self, value):
#         """Ensure email is unique"""
#         if User.objects.filter(email=value).exists():
#             raise serializers.ValidationError("Email already registered.")
#         return value

#     def validate_phone_number(self, value):
#         """Ensure phone number is unique and exactly 10 digits"""
#         if len(value) != 10:
#             raise serializers.ValidationError("Phone number must be exactly 10 digits.")
#         if User.objects.filter(phone_number=value).exists():
#             raise serializers.ValidationError("Phone number already registered.")
#         return value

#     def create(self, validated_data):
#         """Create user instance with uploaded image"""
#         return User.objects.create(**validated_data)
    

class UserRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True, max_length=15)
    # fingerprint_data = serializers.CharField(required=False, allow_null=True)
    user_image = serializers.ImageField(required=True)  # Ensure image is mandatory


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
        if len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already registered.")
        return value
    
    def validate_user_image(self, value):
        """Ensure user_image is provided"""
        if not value:
            raise serializers.ValidationError("User image is required.")
        return value

    def create(self, validated_data):
        """Create user instance with uploaded image"""
        return User.objects.create(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    user_image_url = serializers.SerializerMethodField()
    verified_by = serializers.CharField(source='verified_by.username', required=False, allow_null=True)
    verified_at = serializers.DateTimeField(required=False, allow_null=True, format="%Y-%m-%d %H:%M:%S")


    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'qr_verified', 'user_image_url', 'verified_by', 'verified_at']
    
    def get_user_image_url(self, obj):
        if obj.user_image:
            return obj.user_image.url
        return None



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=4)

    
