from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile', views.profile, name='profile'),
    path('transactions/<str:pageElem>/<str:page>/', views.transactions, name='transactions'),
    path('report', views.report, name='report'),
    path('help', views.helpPage, name='help'),
    path('delete', views.delete, name='delete'),
    # path('api/chart/data/', views.ChartData.as_view()),
    path('api/chart/data/', views.home, name='home'),

]
