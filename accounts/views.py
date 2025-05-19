# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import SignUpForm, LoginForm
from .models import CustomUser, Contact, EmailVerification, cipher_suite
from django.http import HttpResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from google.oauth2 import id_token
from google.auth.transport import requests
from twilio.rest import Client
from django.conf import settings
from twilio.base.exceptions import TwilioRestException
import random
import uuid
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site

def phone_login(request):
    print(f"Method: {request.method}")
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        verification = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID) \
                       .verifications.create(to=phone_number, channel='sms')
        print(f"Verification sent: {verification.sid}")
        request.session['phone_number'] = phone_number
        return redirect('verify_otp')
    return render(request, 'phone_login.html')

def verify_otp(request):
    print(f"Method: {request.method}")
    if request.method == 'POST':
        otp = request.POST.get('otp')
        phone_number = request.session.get('phone_number')
        print(f"OTP: {otp}, Phone: {phone_number}")
        if not phone_number:
            messages.error(request, "Session expired. Please start over.")
            return redirect('phone_login')
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID) \
                                        .verification_checks.create(to=phone_number, code=otp)
            print(f"Verification status: {verification_check.status}")
            if verification_check.status == 'approved':
                user, created = CustomUser.objects.get_or_create(
                    phone_number=phone_number,
                    defaults={
                        'username': f'phone_{phone_number}',
                        'email': f'phone_{phone_number}@example.com'
                    }
                )
                login(request, user)
                messages.success(request, "Logged in successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Invalid OTP.")
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
        except TwilioRestException as e:
            print(f"pets verify error: {str(e)}")
            messages.error(request, f"Verification failed: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            messages.error(request, "An error occurred. Please try again.")
    return render(request, 'verify_otp.html')

def index_view(request):
    return render(request, 'index.html')

def google_login(request):
    return render(request, 'google_login.html')

def profile_view(request):
    return render(request, 'profile.html')

def contact(request):
    return render(request, 'contactus.html')

@csrf_exempt
def auth_receiver(request):
    if request.method == 'POST':
        token = request.POST.get('credential')
        try:
            user_data = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
            )
            print(f"Google User Data: {user_data}")
            email = user_data['email']
            username = user_data.get('given_name', email.split('@')[0])
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': username[:30],
                }
            )
            if created:
                user.set_unusable_password()
                user.email_verified = True
                user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            print(f"Logged in user: {user.username}")
            return redirect('profile')
        except ValueError:
            return HttpResponse("Invalid Google token", status=403)
    return HttpResponse("Method not allowed", status=405)

def signup_view(request):
    if request.method == 'POST':
        signup_form = SignUpForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            password = signup_form.cleaned_data['password']
            user.set_password(password)
            user.encrypted_password = cipher_suite.encrypt(password.encode())
            user.email_verified = False
            user.save()
            # CHANGED: Check for existing EmailVerification and delete if exists
            EmailVerification.objects.filter(email=user.email).delete()
            verification = EmailVerification.objects.create(
                email=user.email,
                token=uuid.uuid4(),
                expires_at=timezone.now() + timezone.timedelta(hours=24)
            )
            verification_link = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': str(verification.token)})
            )
            subject = 'Verify Your Email - Case Companion'
            message = f'Hi,\n\nPlease click the link below to verify your email:\n{verification_link}\n\nThis link is valid for 24 hours.\n\nThank you,\nCase Companion Team'
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Account created! Please check your inbox to verify your email.')
            except Exception as e:
                messages.error(request, f'Failed to send verification email: {str(e)}')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        signup_form = SignUpForm()
    return render(request, 'login.html', {'signup_form': signup_form, 'form_type': 'signup'})

def verify_email_view(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
        if verification.expires_at < timezone.now():
            messages.error(request, 'The verification link has expired.')
            verification.delete()
            return redirect('login')
        if not verification.is_verified:
            verification.is_verified = True
            verification.save()
            user = CustomUser.objects.get(email=verification.email)
            user.email_verified = True
            user.save()
            verification.delete()
            messages.success(request, 'Your email has been verified! You can now log in.')
            return redirect('login')
        else:
            messages.info(request, 'This email is already verified.')
            return redirect('login')
    except (EmailVerification.DoesNotExist, CustomUser.DoesNotExist):
        messages.error(request, 'Invalid verification link.')
        return redirect('login')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.email_verified:
                    login(request, user)
                    return redirect('chat_room')
                else:
                    messages.error(request, 'Please verify your email before logging in.')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'login_form': form, 'form_type': 'login'})

def logout_view(request):
    logout(request)
    return redirect('index')

def password_reset_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                current_site = get_current_site(request)
                protocol = 'https' if request.is_secure() else 'http'
                domain = current_site.domain
                subject = 'Password Reset Request - Case Companion'
                message = render_to_string('password_reset_email.html', {
                    'user': user,
                    'uid': uid,
                    'token': token,
                    'protocol': protocol,
                    'domain': domain,
                })
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'A password reset link has been sent to your email.')
            else:
                messages.error(request, 'No account found with this email.')
        else:
            messages.error(request, 'Please enter a valid email.')
    return redirect('login')

@method_decorator(csrf_exempt, name='dispatch')
class AuthGoogle(APIView):
    def post(self, request, *args, **kwargs):
        try:
            user_data = self.get_google_user_data(request)
        except ValueError:
            return HttpResponse("Invalid Google token", status=403)
        email = user_data["email"]
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "username": user_data.get("given_name", email.split('@')[0]),
                "first_name": user_data.get("given_name", ""),
            }
        )
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('profile')

    @staticmethod
    def get_google_user_data(request: HttpRequest):
        token = request.POST['credential']
        return id_token.verify_oauth2_token(
            token, Requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
        )

def profile_view(request):
    if request.user.is_authenticated:
        return render(request, 'profile.html', {'user': request.user})
    return redirect('google_login')

def contact_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        message = request.POST.get('message')
        try:
            contact = Contact.objects.create(
                email=email,
                contact_number=contact_number,
                message=message
            )
            subject = 'Query Received - Case Companion'
            email_message = (
                f"Dear {email},\n\n"
                "Thank you for contacting Case Companion. We have received your query:\n\n"
                f"Contact Number: {contact_number}\n"
                f"Message: {message}\n\n"
                "Our team is working on it, and we’ll get back to you soon.\n\n"
                "Best regards,\n"
                "The Case Companion Team"
            )
            send_mail(
                subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Your query has been submitted successfully! A confirmation email has been sent.')
        except Exception as e:
            messages.error(request, f'Error submitting query: {str(e)}')
        return redirect('contact')
    return render(request, 'contact.html')