from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, status, generics

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .serializers import UserDisplaySerializer

from django.conf import settings
from functools import wraps
from django.core.mail import EmailMessage
from django.template import loader
from django.core.mail import send_mail
from datetime import datetime
from django.db.models import Q
import time
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from .applayer import *


def activation_email(user, link):
    subject = "Email Verification"
    html_message = loader.render_to_string(
        settings.BASE_DIR + '/templates/activation_email.html',
        {
            'link': str(link),
            'name': str(user.first_name),
        }
    )
    message = ''
    from django.core.mail import send_mail
    send_mail(subject, message, settings.EMAIL_HOST_USER, [
              user.email], fail_silently=True, html_message=html_message)


@permission_classes((AllowAny, ))
class UserRegistration(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data

        try:
            email = data['email']
            if not User.objects.filter(email=email, is_active=True).count() == 0:
                result = {"status": False,
                          "message": "Email is already register with us"}
                return Response(result, status=status.HTTP_208_ALREADY_REPORTED)
            elif not User.objects.filter(email=email, is_active=False).count() == 0:
                existing = True
                result = {"status": False,
                          "message": "Email is already register with us, verification is pending, Please check registered email id"}
                return Response(result, status=status.HTTP_208_ALREADY_REPORTED)
            else:
                existing = False
        except:
            result = {"status": False, "message": "Please Enter the Email"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        try:
            password = data['password']
        except:
            result = {"status": False, "message": "Password is Missing"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        userobj = User()
        userobj.first_name = data['first_name']
        userobj.last_name = data['last_name']
        userobj.email = email
        userobj.username = email
        userobj.is_active = False
        userobj.set_password(password)
        userobj.save()

        activation_link = 'http://' + request.META['HTTP_HOST'] + '/api/v1/confirm-email/' + urlsafe_base64_encode(
            force_bytes(userobj.id)) + '/' + account_activation_token.make_token(userobj) + '/'

        activation_email(userobj, activation_link)

        result = {"status": True, "message": "Signed  up Successfully"}
        return Response(result, status=status.HTTP_201_CREATED)


@permission_classes((AllowAny, ))
class ConfirmEmail(APIView):

    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            result = {"status": True, "message": "User is activated"}
            return Response(result, status=status.HTTP_200_OK)
        else:
            logging.critical('Activation link is invalid!')
            result = {"status": False, "message": "Activation link is invalid!"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)