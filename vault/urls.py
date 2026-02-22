from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('member/<int:pk>/', views.member_detail, name='member_detail'),
    path('member/add/', views.add_member, name='add_member'),
    path('member/<int:pk>/edit/', views.edit_member, name='edit_member'),
    path('document/<int:pk>/', views.document_viewer, name='document_viewer'),
    path('document/<int:pk>/download/', views.document_download, name='document_download'),
    path('document/<int:pk>/convert/', views.document_convert, name='document_convert'),
    path('document/<int:pk>/rename/', views.document_rename, name='document_rename'),
    path('document/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('upload/', views.upload, name='upload'),
]
