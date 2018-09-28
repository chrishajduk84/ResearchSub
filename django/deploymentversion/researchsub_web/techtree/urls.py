# techtree/urls.py
from django.conf.urls import url
from techtree import views


urlpatterns = [
    url(r'^$', views.HomePageView.as_view()),
    url(r'^graph/',views.GraphView.as_view()),
    ]
