from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def send_verification_email(user_id, token):
    """
    Background task: sends email verification link to the user.
    Runs via Celery so registration API responds instantly.
    """
    try:
        user = User.objects.get(id=user_id)
        verification_url = f"http://localhost:8000/api/accounts/verify-email/?token={token}"

        send_mail(
            subject='Verify your SmartBooks account',
            message=f"""
Hi {user.first_name},

Welcome to SmartBooks! Please verify your email address by clicking the link below:

{verification_url}

This link expires in 24 hours.

If you did not create an account, please ignore this email.

— The SmartBooks Team
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except User.DoesNotExist:
        pass