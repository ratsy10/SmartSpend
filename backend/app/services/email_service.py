import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_otp_email(to_email: str, otp_code: str):
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        print(f"[MOCK EMAIL] SMTP not fully configured. OTP for {to_email} is {otp_code}")
        return False

    msg = MIMEMultipart()
    msg['From'] = settings.smtp_user
    msg['To'] = to_email
    msg['Subject'] = "SmartSpend - Verify Your Account"

    body = f"""
    Welcome to SmartSpend!
    
    Your verification code is: {otp_code}
    
    This code will expire in 10 minutes.
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
            
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL] OTP sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Error sending email to {to_email}: {str(e)}")
        return False
