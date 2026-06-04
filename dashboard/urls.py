"""Dashboard URL Configuration"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('upload/', views.upload_cv, name='upload_cv'),
    path('report/<uuid:report_id>/', views.view_report, name='view_report'),
    path('report/<uuid:report_id>/status/', views.report_status, name='report_status'),
    path('roadmap/<uuid:report_id>/', views.roadmap_view, name='roadmap_view'),
    path('profile/', views.profile_view, name='profile'),
]
