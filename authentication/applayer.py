from __future__ import print_function
from usermgmt.settings import SECRET_KEY
import boto3
import botocore.exceptions
import hmac
import hashlib
import base64
import json
import uuid
import os
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from six import text_type


def get_secret_code(username):
    msg = username + SECRET_KEY
    dig = hmac.new(str(SECRET_KEY).encode('utf-8'),
                   msg=str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    code = base64.b64encode(dig).decode()
    return code


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return (
            text_type(user.pk) + text_type(timestamp) +
            text_type(user.is_active)
        )

account_activation_token = AccountActivationTokenGenerator()
