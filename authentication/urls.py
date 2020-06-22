from django.urls import path
from .views import *


urlpatterns = [
	path('registration/', UserRegistration.as_view()),
	path('confirm-email/<slug:uidb64>/<slug:token>/', ConfirmEmail.as_view(), name='confirm_email'),
]