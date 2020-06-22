from django.contrib.auth.models import User, Group
from rest_framework import serializers


class UserDisplaySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'first_name']