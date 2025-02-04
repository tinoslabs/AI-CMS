import logging
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .models import User
from .serializers import UserRegistrationSerializer, LoginSerializer, UserSerializer
from .utils import generate_secure_qr_code, send_email_with_qr, compare_fingerprints
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from hashlib import sha256
from django.utils import timezone
from django.shortcuts import render
# # from deepface import DeepFace
# import cv2
# from django.http import JsonResponse


logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')

class RegistrationRateThrottle(AnonRateThrottle):
    rate = '24/hour'  # Limit registration attempts

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic  # Ensures rollback if something fails
def register_user(request):
    try:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            user_image = serializer.validated_data['user_image']  # Now mandatory
            phone_number = serializer.validated_data['phone_number']  # Now mandatory
            designation = serializer.validated_data['designation']

         
            try:
                qr_data, qr_buffer = generate_secure_qr_code(username)

                email_sent = send_email_with_qr(email, username, qr_buffer)

                if not email_sent:
                    return Response({"error": "Failed to send QR code email. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                return Response({"error": "Invalid email or email sending failed."}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create(
                username=username,
                email=email,
                phone_number=phone_number,  # Now mandatory
                designation=designation,
                qr_code_data=qr_data,
                user_image=user_image,  # Now mandatory
                qr_delivered=True,
                qr_verified=False,
                # fingerprint_template = fingerprint_template,
                # fingerprint_template_hash = fingerprint_template_hash,                
                fingerprint_verified = False
            )

            qr_buffer.seek(0)
            user.qr_code.save(f'qr_code_{username}.jpg', ContentFile(qr_buffer.getvalue()), save=True)

            response_data = {
                "message": "Registration successful. Please check your email for the QR code.",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "designation":designation,
                    "user_image_url": request.build_absolute_uri(user.user_image.url) if user.user_image else None,
                    "qr_code_url": user.qr_code.url if user.qr_code else None,
                    "delivered": user.qr_delivered
                }
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            print("Serializer validation failed:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        print("Unexpected error:", e)
        return Response({"error": "Registration failed. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View: Verify Fingerprint and Return Account Details
@api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Assuming the user is authenticated (JWT or other method)
def verify_fingerprint(request):
    fingerprint_data = request.data.get('fingerprint_data')

    if not fingerprint_data:
        return Response({"error": "Fingerprint data is required."}, status=400)

    try:
        # Step 1: Find the user by matching the fingerprint hash
        users_with_fingerprints = User.objects.exclude(fingerprint_template_hash__isnull=True)

        # Step 2: Compare the fingerprint data with the stored template hash
        for user in users_with_fingerprints:
            if compare_fingerprints(user.fingerprint_template_hash, fingerprint_data):
                # Step 3: If match found, mark fingerprint as verified and return user details
                # user.fingerprint_verified = True
                user.fingerprint_verified = False
                user.save()

                # Return the user account details
                return Response({
                    "message": "Fingerprint verified successfully.",
                    "user": {
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "fingerprint_verified": user.fingerprint_verified,
                        "user_image_url": request.build_absolute_uri(user.user_image.url) if user.user_image else None,
                    }
                }, status=200)

        # If no match found
        return Response({"error": "Fingerprint not recognized."}, status=400)

    except Exception as e:
        # Handle unexpected errors
        return Response({"error": "An error occurred during fingerprint verification."}, status=500)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_qr_code(request):
    qr_data = request.data.get('qr_code_data')
    
    if not qr_data:
        return Response({"error": "QR code data is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(qr_code_data=qr_data)

        if user.qr_verified:
            return Response({"error": "This QR code has already been verified."}, status=status.HTTP_400_BAD_REQUEST)

        # user.qr_verified = True
        user.qr_verified = False

        user.verified_by = request.user
        user.verified_at = timezone.now()
        user.save()
        
        # return Response({
        #     "message": "QR code verified successfully.",
        #     "user": {
        #         "username": user.username,
        #         "email": user.email,
        #         "qr_code_verified": user.qr_verified,
        #         "user_image_url": request.build_absolute_uri(user.user_image.url) if user.user_image else None,
        #         "verified_by": user.verified_by,
        #         "verified_at": user.verified_at
        #     }
        # }, status=status.HTTP_200_OK)
        
        user_serializer = UserSerializer(user)

        # Return the serialized user data as a response
        return Response({
            "message": "QR code verified successfully.",
            "user": user_serializer.data
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        
        return Response({"error": "Invalid QR code data. User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        
        return Response({"error": "An unexpected error occurred during verification."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and return JWT tokens.
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(username=email, password=password)  # Authenticate using email

        if user is not None:
            if not user.is_active:
                return Response({'error': 'User account is inactive'}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'username': user.username,
                    'role': user.role  # Return user role if needed
                }
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logs out user by blacklisting the refresh token.
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()  # Blacklist the refresh token

        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def verify_face(request):
#     """
#     Face verification using DeepFace. Returns the facial area and the matched name.
#     """

#     # Get uploaded image from request
#     face_image = request.FILES.get('face_image')
    
#     if not face_image:
#         return JsonResponse({"error": "No face image provided"}, status=400)

#     # Save the uploaded image temporarily
#     temp_path = f"/tmp/{face_image.name}"
#     with open(temp_path, "wb") as f:
#         for chunk in face_image.chunks():
#             f.write(chunk)

#     try:
#         # Perform face recognition
#         dfs = DeepFace.find(
#             img_path=temp_path,
#             db_path="media/user_images",
#             model_name="Facenet512",
#             enforce_detection=False
#         )

#         if not dfs or len(dfs[0]) == 0:
#             return JsonResponse({"error": "No matching face found"}, status=404)

#         # Get the first match
#         df = dfs[0]
#         matched_instance = df.iloc[0]
        
#         # Extract image path and bounding box coordinates
#         source_path = matched_instance["identity"]
#         x, y, w, h = int(matched_instance["target_x"]), int(matched_instance["target_y"]), int(matched_instance["target_w"]), int(matched_instance["target_h"])

#         # Read and crop the matched face
#         source_img = cv2.imread(source_path)
#         face_cropped = source_img[y:y+h, x:x+w]

#         # Convert cropped image to JPEG
#         _, buffer = cv2.imencode(".jpg", face_cropped)
#         face_bytes = BytesIO(buffer)

#         # Convert to Django's InMemoryUploadedFile for easy response handling
#         face_file = InMemoryUploadedFile(face_bytes, None, "face.jpg", "image/jpeg", face_bytes.getbuffer().nbytes, None)

#         # Extract the matched person's name (filename without extension)
#         matched_name = os.path.splitext(os.path.basename(source_path))[0]

#         # Return response with name and image
#         return JsonResponse({
#             "matched_name": matched_name,
#             "cropped_face": face_file.name
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

#     finally:
#         # Clean up temp file
#         if os.path.exists(temp_path):
#             os.remove(temp_path)
