from . import views
from django.urls import path
from django.contrib import admin
from account.views import UserloginView, DashboardView, HomePageView
from django.contrib.auth import views as auth_views
from .views import UserListView, UserDetailView, ControlListView, UserCreateView, ControlCreateView, EditControlView, DhanKillProcessLogListView


urlpatterns = [
    # landing page
    path('', views.HomePageView.as_view(), name='home'),
    # login 
    path('login/', views.UserloginView.as_view(), name = 'login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),  # Add this line
    # dashboard 
    path('dashboard', views.DashboardView.as_view(), name='dashboard'),

    
    path('create-user/', UserCreateView.as_view(), name='create_user'),
    path('create-control/', ControlCreateView.as_view(), name='create_control'),

 
    path('users/', UserListView.as_view(), name='manage_user'),  # Manage Users URL
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),  # User Detail URL (optional)
    path('delete/<int:pk>/', views.user_delete, name='user_delete'),


    path('controls/', ControlListView.as_view(), name='manage_controls'),  # Manage Controls URL
    path('controls/<int:pk>/', EditControlView.as_view(), name='edit-control'),  # User Detail URL (optional)

    path('dhan_kill_logs/', DhanKillProcessLogListView.as_view(), name='dhan-kill-log-list'),
    path('dashboard/<slug:slug>/', DashboardView.as_view(), name='dashboard'),
    # path('dashboard/<slug:slug>/<timeperiod:timeperiod>', DashboardView.as_view(), name='dashboard'),

    path('close-all-positions/', views.close_all_positions, name='close_all_positions'),
    path('clear-kill-log/', views.clear_kill_log, name='clear_kill_log'),
    path('daily-account-overview/', views.DailyAccountOverviewListView.as_view(), name='daily_account_overview_list'),
    path('check-log-status/', views.check_log_status, name='check_log_status'),  # Add the URL for the status check

    path('activate_kill_switch/', views.activate_kill_switch, name='activate_kill_switch'),

]

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/orders/<str:username>/", consumers.OrderUpdateConsumer.as_asgi()),
]