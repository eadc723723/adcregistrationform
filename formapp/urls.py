#urls.py
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('register_student/', views.register_student, name='register_student'),
    path('register_student/<str:agent_code>/', views.register_student, name='register_student_with_agent'),
    path('student_registration_success/', views.student_registration_success, name='student_registration_success'),
    path('student_registration_success/<str:agent_code>/', views.student_registration_success, name='student_registration_success_with_agent'),
    path('get-registration-forms/', views.get_registration_forms, name="get_registration_forms"),
    path('get_terms/', views.get_terms, name='get_terms'),  # Add this line
    path('dashboard/', views.dashboard, name='dashboard'),
    path('registration_success/<int:student_id>/', views.registration_success, name='registration_success'),
    path('student-details/<int:student_id>/', views.student_details, name='student_details'),
    path('validate-agent-code/', views.validate_agent_code, name='validate_agent_code'),
    path('validate-id-no/', views.validate_id_no, name='validate_id_no'),
    path('preview/', views.preview_students, name='preview_students'),
    path('delete_students/', views.delete_students_by_date, name='delete_students'),

    path('api/students/', views.StudentList.as_view(), name='student-list'),
    path('api/classes/', views.ClassList.as_view(), name='class-list'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
