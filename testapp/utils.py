# utils.py
import qrcode
from io import BytesIO
from typing import Tuple
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from email.mime.image import MIMEImage
import hashlib
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

def hash_qr_data(qr_data: str) -> str:
    """Hash QR data with additional salt for security."""
    salted_data = f"{qr_data}{settings.SECRET_KEY}"
    return hashlib.sha256(salted_data.encode()).hexdigest()

def generate_secure_qr_code(username: str) -> Tuple[str, BytesIO]:
    """
    Generates a secure QR code.
    
    Args:
        username: The username to generate QR code for
        
    Returns:
        Tuple containing QR data string and BytesIO buffer with QR image
    """
    try:
        # Generate unique ID with timestamp for better uniqueness
        unique_id = get_random_string(32)
        qr_data = f"EVENT-{settings.EVENT_ID}-{username}-{unique_id}"
        qr_data = hash_qr_data(qr_data)
        
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
        buffer.seek(0)
        
        return qr_data, buffer
    except Exception as e:
        logger.error(f"QR generation error: {str(e)}")
        raise

def send_email_with_qr(email: str, username: str, qr_buffer: BytesIO) -> bool:
    """
    Sends email with QR code using transaction and retry mechanism.
    """
    MAX_RETRIES = 3
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            with transaction.atomic():
                context = {
                    'username': username,
                    'event_name': settings.EVENT_NAME,
                    'event_date': settings.EVENT_DATE,
                    'event_venue': getattr(settings, 'EVENT_VENUE', ''),
                    'event_time': getattr(settings, 'EVENT_TIME', ''),
                }
                
                html_content = render_to_string('emails/mail_index.html', context)
                text_content = render_to_string('emails/qr_code.txt', context)

                email_message = EmailMultiAlternatives(
                    subject=f"Your Registration QR Code for {settings.EVENT_NAME}",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                
                # Attach QR code
                qr_buffer.seek(0)
                qr_image = MIMEImage(qr_buffer.read())
                qr_image.add_header('Content-ID', '<qr_code>')
                qr_image.add_header('Content-Disposition', 'inline')
                qr_image.add_header('X-Attachment-Id', 'qr_code')
                email_message.attach(qr_image)
                
                email_message.attach_alternative(html_content, "text/html")
                
                email_message.send(fail_silently=False)
                logger.info(f"Successfully sent registration email to {email}")
                return True
                
        except Exception as e:
            retry_count += 1
            logger.warning(f"Email sending attempt {retry_count} failed: {str(e)}")
            if retry_count == MAX_RETRIES:
                logger.error(f"Failed to send email after {MAX_RETRIES} attempts: {str(e)}")
                raise
    
    return False