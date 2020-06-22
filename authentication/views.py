from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, status, generics
from rest_framework.pagination import LimitOffsetPagination

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

from django.contrib.auth import login as django_login, logout as django_logout, authenticate, get_user_model
import requests


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

        try:
            first_name = data['first_name']
        except:
            first_name = ""

        try:
            last_name = data['last_name']
        except:
            last_name = ""

        userobj = User()
        userobj.first_name = first_name
        userobj.last_name = last_name
        userobj.email = email
        userobj.username = email
        userobj.is_active = False
        userobj.set_password(password)
        userobj.save()

        activation_link = 'http://' + request.META['HTTP_HOST'] + '/api/v1/confirm-email/' + urlsafe_base64_encode(
            force_bytes(userobj.id)) + '/' + account_activation_token.make_token(userobj) + '/'

        activation_email(userobj, activation_link)

        result = {"status": True, "message": "Signed  up Successfully. Verification link send to the email"}
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
            userobj = {}
            userobj["first_name"] = user.first_name
            userobj["last_name"] = user.last_name
            userobj["email"] = user.email
            userobj["status"] = 'Active'
            result = {"status": True, "message": "User is activated",
                      "user_details": userobj}
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {
                "status": False, "message": "Activation link is invalid or already activated!"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((AllowAny, ))
class Login(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        # print(data)
        try:
            email = data['email']
            profile = User.objects.filter(email=email)
            if profile.count() == 0:
                result = {"status": False,
                          "message": "Email is not registered with us."}
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            elif profile[0].is_active == False:
                result = {"status": False,
                          "message": "Account is not Active, Please activate your account, check your email for the link."}
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
        except:
            result = {"status": False, "message": "Email is Missing"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        try:
            password = data['password']
        except:
            result = {"status": False, "message": "Password is Missing"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        url = "http://127.0.0.1:8080/api/token/"

        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
        }

        payload = {
            "username": email,
            "password": password
        }

        resp = requests.request(
            "POST", url, data=json.dumps(payload), headers=headers)
        values = json.loads(resp.text)
        if resp.status_code == 200:
            values['first_name'] = profile[0].first_name
            values['last_name'] = profile[0].last_name
            values['email'] = profile[0].email

            result = {"status": True,
                      "message": "User Logged in successfully", "result": values}
            return Response(result, status=status.HTTP_200_OK)
        else:
            print("error in login")
            result = {"status": False, "message": "Login failed"}
            return Response(result, status=status.HTTP_401_UNAUTHORIZED)


permission_classes((AllowAny, ))
class Logout(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        # print(data)
        try:
            token = data['token']
        except:
            result = {"status": False, "message": "Token Missing"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        print(token)
        url = "http://127.0.0.1:8080/api/token/refresh/"
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
        }
        payload = {
            "refresh": token
        }
        resp = requests.request(
            "POST", url, data=json.dumps(payload), headers=headers)
        values = json.loads(resp.text)
        print(resp.text)

        result = {"status": True, "message": "User Logged Out Successfully"}
        return Response(result, status=status.HTTP_200_OK)


class ChangePassword(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)

        try:
            current_password = data['current_password']

            url = "http://127.0.0.1:8080/api/token/"
            headers = {
                'Content-Type': "application/json",
                'cache-control': "no-cache",
            }
            payload = {
                "username": request.user.username,
                "password": current_password
            }
            resp = requests.request(
                "POST", url, data=json.dumps(payload), headers=headers)
            values = json.loads(resp.text)
            if not resp.status_code == 200:
                result = {"status": False,
                          "message": "Current Password is incorrect"}
                return Response(result, status=status.HTTP_401_UNAUTHORIZED)
        except:
            result = {"status": False,
                      "message": "Current Password is Missing"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_password = data['new_password']
        except:
            result = {"status": False, "message": "New Password is Missing"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=request.user.id)
        user.set_password(new_password)
        user.save()

        result = {"status": True, "message": "Password changed successfully"}
        return Response(result, status=status.HTTP_200_OK)


class UserList(generics.ListAPIView):

    permission_classes = (IsAuthenticated,)
    queryset = User.objects.exclude(is_superuser=True).order_by('-id')
    serializer_class = UserDisplaySerializer
    pagination_class = LimitOffsetPagination

    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            user_id = data['user_id']
        except:
            result = {"status": False, "message": "User ID is missing"}
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        user_det = get_object_or_404(User.objects.all(), id=user_id)
        serializer = UserDisplaySerializer(user_det, many=False)
        return Response({"user_details": serializer.data})
