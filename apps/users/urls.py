# backend/apps/users/urls.py

from django.urls import path
from .views import LoginView, RegisterView, LogoutView



urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),  # 添加登录的 URL 路由
    path('register/', RegisterView.as_view(), name='register'),  # 添加注册的 URL 路由
    path('logout/', LogoutView.as_view(), name='logout'),  # 添加登出的 URL 路由
]
