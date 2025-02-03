import qrcode
from io import BytesIO
from typing import Tuple
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from email.mime.image import MIMEImage
import hashlib
from hashlib import sha256
import logging
logger = logging.getLogger(__name__)

#  for hashing the QR Data
def hash_qr_data(qr_data: str) -> str:
    return hashlib.sha256(qr_data.encode()).hexdigest()


def generate_secure_qr_code(username: str) -> Tuple[str, BytesIO]:
    """
    Generates a secure QR code with a unique identifier for user verification.
    
    Args:
        username: The username to generate QR code for
        
    Returns:
        Tuple containing QR data string and BytesIO buffer with QR image
    """
    unique_id = get_random_string(32)
    qr_data = f"EVENT-{settings.EVENT_ID}-{username}-{unique_id}"
    
    qr_data = hash_qr_data(qr_data) # for hashing
    
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
        buffer.seek(0)  # Reset buffer to the start
        
        return qr_data, buffer
    except Exception as e:
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
        context = {
            'username': username,
            'event_name': settings.EVENT_NAME,
            'event_date': settings.EVENT_DATE,
        }
        
        html_content = render_to_string('emails/index.html', context)
        text_content = render_to_string('emails/qr_code.txt', context)

        # Create the email message
        email_message = EmailMultiAlternatives(
            subject=f"Your QR Code for {settings.EVENT_NAME}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            reply_to=[settings.EVENT_SUPPORT_EMAIL],
        )
        
        # Attach QR code with proper headers
        qr_buffer.seek(0)
        qr_image = MIMEImage(qr_buffer.read())
        qr_image.add_header('Content-ID', '<qr_code>')
        qr_image.add_header('Content-Disposition', 'inline')
        qr_image.add_header('X-Attachment-Id', 'qr_code')
        email_message.attach(qr_image)
        
        # Attach partner logos
        partner_images = {
            'tinos': 'images/tinos.png',
            'ezone': 'images/ezone.jpg',
            'bbc': 'images/bbc logo-01-01-01-01 (1).png',
            'sentinora': 'images/sentinora.png'
        }
        
        for cid, image_path in partner_images.items():
            try:
                with open(image_path, 'rb') as img:
                    img_data = img.read()
                    img_mime = MIMEImage(img_data)
                    img_mime.add_header('Content-ID', f'<{cid}>')
                    img_mime.add_header('Content-Disposition', 'inline')
                    img_mime.add_header('X-Attachment-Id', cid)
                    email_message.attach(img_mime)
            except Exception as e:
                logger.warning(f"Could not attach partner image {cid}: {str(e)}")

        # Attach HTML version
        email_message.attach_alternative(html_content, "text/html")
        
        # Send the email
        email_message.send(fail_silently=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise


#  Utility function to compare fingerprints using hashed templates
def compare_fingerprints(stored_hash, input_template):
    """
    Compare the stored fingerprint hash with the input template's hash.
    This is faster than comparing the entire fingerprint templates.
    """
    input_hash = sha256(input_template).hexdigest()
    return stored_hash == input_hash

