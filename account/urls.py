from . import views
from django.urls import path
from django.contrib import admin
from account.views import UserloginView, DashboardView, HomePageView
from django.contrib.auth import views as auth_views
from .views import UserListView, UserDetailView, ControlListView, UserCreateView


urlpatterns = [
    # landing page
    # path('', views.HomePageView.as_view(), name='home'),
    # login 
    path('', views.UserloginView.as_view(), name = 'login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),  # Add this line
    # dashboard 
    path('dashboard', views.DashboardView.as_view(), name='dashboard'),
    # auth code view  
    path('users/', UserListView.as_view(), name='manage_user'),  # Manage Users URL
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),  # User Detail URL (optional)
    path('controls/', ControlListView.as_view(), name='manage_controls'),  # Manage Controls URL

    path('create-user/', UserCreateView.as_view(), name='create_user'),
    path('postback-fetch/', views.dhan_postback, name='dhan_postback'),  

    
]