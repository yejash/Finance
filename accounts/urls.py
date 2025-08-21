from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('about/',views.about_view, name='about'),
    path('expenses/',views.expenses_view, name='expenses'),
    path('greeting/', views.greeting_view, name='greeting')
]
