from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from background_task import background


@background(schedule=1)
def send_mail(otp, email):
    html_message = render_to_string(
        'register.html', {"otp":otp}
    )
    email = EmailMessage("OTP for Registration", html_message, to=[email])
    email.content_subtype = "html"
    email.send()         