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
from adminapp.models import Testimonial
from .serializers import (
    UserLoginSerializer, UserSerializer,
    ParticipantRegistrationSerializer, ParticipantSerializer
)
from .utils import generate_secure_qr_code, send_email_with_qr
import logging
from django.shortcuts import render
from django.core.files.base import ContentFile
from deepface import DeepFace
import cv2
import numpy as numpy
from django.conf import settings
import os
from django.http import JsonResponse


logger = logging.getLogger(__name__)

def index(request):
    testimonials = Testimonial.objects.all()
    return render(request, 'index.html', {'testimonials':testimonials})

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


def verify_face_api(request):
    
    if request.method == "POST":
        image = request.FILES.get('image')
        
        face_image = cv2.imdecode(numpy.frombuffer(image.read() , numpy.uint8), cv2.IMREAD_UNCHANGED)
        
        dfs = DeepFace.find(
        img_path=face_image,
        db_path = os.path.join(settings.BASE_DIR, 'media', 'participant_images'),
        enforce_detection=False
        )
        face_data = []
        for df in dfs:
        
            for index, instance in df.iterrows():
                if instance["distance"] >0.1:
                    source_path = instance["identity"]
                    # extract facial area of the source image
                    x = instance["target_x"]
                    y = instance["target_y"]
                    w = instance["target_w"]
                    h = instance["target_h"]
                    # Get the base filename
                    file_name = os.path.basename(source_path)  # Aaron_Diaz.jpg

                    # Remove the extension
                    name_without_extension, _ = os.path.splitext(file_name)  # Aaron_Diaz
                    face_data.append({"x":x, "y":y, "width": w, "height":h, "name":name_without_extension})

        return JsonResponse({"faces": face_data})  # JSON Response
        # return render(request,'verify_face.html')
    print("not post")
    return render(request,'verify_face.html')
    

def verify_face(request):
    return render(request,'verify_face.html')

import os
import zipfile
from io import BytesIO
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Participant



@api_view(["GET"])
# @permission_classes([IsAuthenticated])  # Require JWT Token
def export_participants_to_excel(request):
    """REST API to export participants' details to an Excel file including images."""
    fields = [
        "username", "email", "phone_number", "designation", "user_image",
        "qr_code", "qr_code_data", "qr_delivered", "qr_verified",
        "registered_by", "verified_by", "verified_at", "created_at", "updated_at"
    ]

    participants = Participant.objects.all().values(*fields)

    # Create Excel workbook and sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Participants"

    # Define headers
    headers = ["Username", "Email", "Phone Number", "Designation", "User Image",
               "QR Code", "QR Code Data", "QR Delivered", "QR Verified",
               "Registered By", "Verified By", "Verified At", "Created At", "Updated At"]
    
    ws.append(headers)

    # Set column widths & row heights (for images)
    column_widths = [20, 30, 15, 20, 15, 15, 20, 10, 10, 20, 20, 20, 20, 20]
    for i, width in enumerate(column_widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

    img_height = 50  # Set row height to fit images
    for row_idx in range(2, len(participants) + 2):
        ws.row_dimensions[row_idx].height = img_height

    media_root = settings.MEDIA_ROOT  # Get media root path

    for idx, participant in enumerate(participants, start=2):  # Start from row 2
        row_data = [
            participant["username"],
            participant["email"],
            participant["phone_number"],
            participant["designation"],
            "",  # Placeholder for user image
            "",  # Placeholder for QR code
            participant["qr_code_data"],
            participant["qr_delivered"],
            participant["qr_verified"],
            participant["registered_by"] or "N/A",
            participant["verified_by"] or "N/A",
            participant["verified_at"].replace(tzinfo=None) if participant["verified_at"] else "",
            participant["created_at"].replace(tzinfo=None) if participant["created_at"] else "",
            participant["updated_at"].replace(tzinfo=None) if participant["updated_at"] else "",
        ]

        # Add row data
        ws.append(row_data)

        # Insert user image
        user_image_path = participant["user_image"]
        if user_image_path:
            full_path = os.path.join(media_root, user_image_path)
            if os.path.exists(full_path):
                img = ExcelImage(full_path)
                img.width, img.height = 50, 50
                img.anchor = f"E{idx}"  # Insert into column E
                ws.add_image(img)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="participants_with_images.xlsx"'

    with BytesIO() as output:
        wb.save(output)
        output.seek(0)
        response.write(output.getvalue())

    return response


@api_view(["GET"])
# @permission_classes([IsAuthenticated])  # Require JWT Token
def download_all_images(request):
    """REST API to create and download a ZIP file containing all participant images."""
    
    zip_buffer = BytesIO()
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)
    media_root = settings.MEDIA_ROOT  # Base directory for media files

    participants = Participant.objects.all()

    for participant in participants:
        if participant.user_image:
            user_image_path = os.path.join(media_root, participant.user_image.name)
            if os.path.exists(user_image_path):
                zip_file.write(user_image_path, f"user_images/{os.path.basename(user_image_path)}")

    zip_file.close()

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="participant_images.zip"'

    return response
