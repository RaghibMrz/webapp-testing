from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('profile', views.profile, name = 'profile'),
    path('transactions', views.transactions, name = 'transactions'),
    path('report', views.report, name = 'report'),
    path('help', views.help, name = 'help'),
    # path('api/chart/data/', views.ChartData.as_view()),
    path('api/chart/data/', views.home, name = 'home'),

]
