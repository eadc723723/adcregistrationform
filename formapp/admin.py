from django.contrib import admin
from .models import RegistrationForms, Student, Class, ID_photo, Agent, Terms

# Register the RegistrationForms model
@admin.register(RegistrationForms)
class RegistrationFormsAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('classes',)  # Display classes as checkboxes

    def __str__(self):
        return self.name

# Register the Student model
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_no', 'email', 'registration_date')
    search_fields = ('name', 'id_no', 'email')

    list_filter = ('gender', 'registration_date')

# Register the Class model
@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('class_type',)
    search_fields = ('class_type',)
    filter_horizontal = ('forms',)  # Display forms as checkboxes

    def __str__(self):
        return self.class_type

# Register the ID_photo model
@admin.register(ID_photo)
class ID_photoAdmin(admin.ModelAdmin):
    list_display = ('student_id_no', 'image')
    search_fields = ('student__name', 'student__id_no')
    
    def student_id_no(self, obj):
        return obj.student.id_no
    student_id_no.short_description = 'Student ID No'


# Register the Agent model
@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('agent_code', 'agent_name')
    search_fields = ('agent_code', 'agent_name')

# Register the Terms model
@admin.register(Terms)
class TermsAdmin(admin.ModelAdmin):
    list_display = ('form_id', 'description')
    search_fields = ('form_id__name', 'description')
