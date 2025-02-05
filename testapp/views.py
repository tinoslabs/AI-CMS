# views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import transaction
from .models import User, Participant
from .serializers import (
    UserLoginSerializer, UserSerializer,
    ParticipantRegistrationSerializer, ParticipantSerializer
)
from .utils import generate_secure_qr_code, send_email_with_qr
import logging
from django.shortcuts import render
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(username=email, password=password)

        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful.',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'username': user.username,
                }
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def register_participant(request):
    try:
        serializer = ParticipantRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        qr_data, qr_buffer = generate_secure_qr_code(validated_data['username'])
        
        participant = Participant.objects.create(
            **validated_data,
            qr_code_data=qr_data,
            registered_by=request.user,
            qr_delivered=True
        )

        qr_buffer.seek(0)
        participant.qr_code.save(
            f'qr_code_{validated_data["username"]}.png',
            ContentFile(qr_buffer.getvalue()),
            save=True
        )

        try:
            email_sent = send_email_with_qr(
                validated_data['email'],
                validated_data['username'],
                qr_buffer
            )
            if not email_sent:
                raise Exception("Failed to send email")
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return Response({
                "error": "Registration successful but email delivery failed. Please try again.",
                "user": ParticipantSerializer(participant).data
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Registration successful. Please check your email for the QR code.",
            "user": ParticipantSerializer(participant).data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({"error": "Registration failed. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_participant(request):
    qr_data = request.data.get('qr_code_data')
    if not qr_data:
        return Response({"error": "QR code data is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        participant = Participant.objects.get(qr_code_data=qr_data)
        
        if participant.qr_verified:
            return Response({"error": "This QR code has already been verified."}, status=status.HTTP_400_BAD_REQUEST)

        # participant.qr_verified = True
        participant.qr_verified = False
        participant.verified_by = request.user
        participant.verified_at = timezone.now()
        participant.save()
        
        return Response({
            "message": "QR code verified successfully.",
            "user": ParticipantSerializer(participant).data,
            "qr_verified_not_unique":True
        }, status=status.HTTP_200_OK)

    except Participant.DoesNotExist:
        return Response({"error": "Invalid QR code data. User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        return Response({"error": "An unexpected error occurred during verification."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
