# todos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Pages
    path('pages/', views.page_list, name='page_list'),
    path('pages/create/', views.page_create, name='page_create'),
    path('pages/<int:page_id>/', views.page_detail, name='page_detail'),
    path('pages/<int:page_id>/edit/', views.page_edit, name='page_edit'),
    path('pages/<int:page_id>/delete/', views.page_delete, name='page_delete'),
    
    # Todos
    path('pages/<int:page_id>/todos/create/', views.todo_create, name='todo_create'),
    path('todos/<int:todo_id>/edit/', views.todo_edit, name='todo_edit'),
    path('todos/<int:todo_id>/delete/', views.todo_delete, name='todo_delete'),
    path('todos/<int:todo_id>/toggle/', views.todo_toggle, name='todo_toggle'),
    
    # Profil
    path('profile/', views.profile_view, name='profile'),
    
    # Recherche
    path('search/', views.search_view, name='search'),
]