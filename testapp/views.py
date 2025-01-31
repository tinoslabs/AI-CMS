import logging
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .models import User
from .serializers import UserRegistrationSerializer
from django.core.exceptions import ValidationError
from .utils import generate_secure_qr_code, send_email_with_qr
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class RegistrationRateThrottle(AnonRateThrottle):
    rate = '24/hour'  # Limit registration attempts

@api_view(['POST'])
@transaction.atomic  # Ensures rollback if something fails
def register_user(request):
    print("Received registration request")
    try:
        print("Request data:", request.data)
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            print("Serializer validation passed")
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            user_image = serializer.validated_data.get('user_image', None)

            try:
                print("Generating QR code")
                qr_data, qr_buffer = generate_secure_qr_code(username)
                print("QR code generated successfully")

                print(f"Sending email to {email}")
                email_sent = send_email_with_qr(email, username, qr_buffer)
                print("Email sent status:", email_sent)

                if not email_sent:
                    print("Email failed to send")
                    return Response({"error": "Failed to send QR code email. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                logger.error(f"Email sending failed for {email}: {str(e)}")
                print("Exception during email sending:", e)
                return Response({"error": "Invalid email or email sending failed."}, status=status.HTTP_400_BAD_REQUEST)

            print("Creating user")
            user = User.objects.create(
                username=username,
                email=email,
                phone_number=serializer.validated_data.get('phone_number', None),
                qr_code_data=qr_data,
                user_image=user_image,
                delivered=True,
                verified=False
            )
            print("User created successfully")

            qr_buffer.seek(0)
            user.qr_code.save(f'qr_code_{username}.png', ContentFile(qr_buffer.getvalue()), save=True)
            print("QR code saved to user model")

            response_data = {
                "message": "Registration successful. Please check your email for the QR code.",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "user_image_url": request.build_absolute_uri(user.user_image.url) if user.user_image else None,
                    "qr_code_url": user.qr_code.url if user.qr_code else None,
                    "delivered": user.delivered
                }
            }
            print("Response data:", response_data)
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            print("Serializer validation failed:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        print("Unexpected error:", e)
        return Response({"error": "Registration failed. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def verify_qr_code(request):
    print("Received QR code verification request")
    qr_data = request.data.get('qr_code_data')
    print("QR Code Data received:", qr_data)
    
    if not qr_data:
        print("Missing QR code data in request")
        return Response({"error": "QR code data is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(qr_code_data=qr_data)
        print("User found for QR code")

        if user.verified:
            print("QR code already verified")
            return Response({"error": "This QR code has already been verified."}, status=status.HTTP_400_BAD_REQUEST)

        user.verified = True
        user.save()
        print("QR code verified and user updated")

        return Response({
            "message": "QR code verified successfully.",
            "user": {
                "username": user.username,
                "email": user.email,
                "qr_code_verified": user.verified,
                "user_image_url": request.build_absolute_uri(user.user_image.url) if user.user_image else None
            }
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        print("Invalid QR code data. User not found.")
        return Response({"error": "Invalid QR code data. User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("Unexpected error during verification:", e)
        return Response({"error": "An unexpected error occurred during verification."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
