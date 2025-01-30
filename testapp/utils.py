import qrcode
from io import BytesIO
from typing import Tuple, Optional
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from io import BytesIO
import hashlib

#  for hashing the QR Data
def hash_qr_data(qr_data: str) -> str:
    return hashlib.sha256(qr_data.encode()).hexdigest()


# logger = logging.getLogger(__name__)

def generate_secure_qr_code(username: str) -> Tuple[str, BytesIO]:
    """
    Generates a secure QR code with a unique identifier for user verification.
    
    Args:
        username: The username to generate QR code for
        
    Returns:
        Tuple containing QR data string and BytesIO buffer with QR image
    """
    # Generate a unique identifier with timestamp and random string
    unique_id = get_random_string(32)
    qr_data = f"EVENT-{settings.EVENT_ID}-{username}-{unique_id}"
    
    ############## qr_data = hash_qr_data(qr_data) for hashing   ############ 

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        buffer = BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
        
        return qr_data, buffer
    except Exception as e:
        # logger.error(f"QR Generation failed for user {username}: {str(e)}")
        raise



def send_email_with_qr(email: str, username: str, qr_buffer: BytesIO) -> bool:
    """
    Sends a multipart email with QR code embedded properly using CID.
    
    Args:
        email: Recipient email address
        username: Username for personalization
        qr_buffer: BytesIO buffer containing QR code image
        
    Returns:
        Boolean indicating success/failure
    """
    try:
        # Prepare email content using templates
        context = {
            'username': username,
            'event_name': settings.EVENT_NAME,
            'event_date': settings.EVENT_DATE,
        }
        
        html_content = render_to_string('emails/qr_code.html', context)
        text_content = render_to_string('emails/qr_code.txt', context)

        # Create the email
        email_message = EmailMultiAlternatives(
            subject=f"Your QR Code for {settings.EVENT_NAME}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            reply_to=[settings.EVENT_SUPPORT_EMAIL],
        )
        
        # Attach the QR code image to the email
        qr_buffer.seek(0)  # Reset buffer to the start
        qr_image = MIMEImage(qr_buffer.read())  # Read the image from the buffer
        qr_image.add_header('Content-ID', '<qr_code>')  # Set CID for inline reference
        email_message.attach(qr_image)

        # Attach HTML content with the CID reference
        email_message.attach_alternative(html_content, "text/html")
        
        # Send the email
        email_message.send(fail_silently=False)
        
        # logger.info(f"QR code email sent successfully to {username}")
        return True
        
    except Exception as e:
        # logger.error(f"Failed to send QR code email to {username}: {str(e)}")
        raise

