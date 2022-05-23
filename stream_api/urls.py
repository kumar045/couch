from django.urls import include, re_path
from .views import *


urlpatterns = [
    re_path('start', StreamAPIView.as_view(), name='start'),


]