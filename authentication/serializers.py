from django.contrib.auth.models import User, Group
from rest_framework import serializers


class UserDisplaySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'last_login']