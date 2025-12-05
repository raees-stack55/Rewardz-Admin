"""
URL configuration for rewardz project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from rentals import views as rentals_views
from users import views as users_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', rentals_views.dashboard, name='home'),
    path('dashboard/', rentals_views.dashboard, name='dashboard'),
    path('rentals/add/', rentals_views.add_rental, name='add_rental'),
    path('rentals/extend/', rentals_views.extend_rental, name='extend_rental'),
    path(
        'students/<int:student_id>/rentals/',
        rentals_views.student_dashboard,
        name='student_dashboard',
    ),
    path('students/add/', users_views.add_student, name='add_student'),
]
