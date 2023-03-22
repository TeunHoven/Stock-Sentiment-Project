from django.urls import path
from . import views

urlpatterns = [
    path('', views.Main, name='Main'),
    path('generate/', views.Generate),
    path('positive/', views.GetPositive),
    path('neutral/', views.GetNeutral),
    path('negative/', views.GetNegative),
    path('all/', views.GetAll),
    path('<slug:slug>/', views.GetCompany),
    path('<slug:slug>/getStockData/', views.getStockData)
]
