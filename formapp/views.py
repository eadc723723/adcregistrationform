from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Student, Class
from .serializers import StudentSerializer, ClassSerializer

from django.views.decorators.http import require_GET
from .forms import Step1Form, Step2Form, Step3Form, IdCardUploadForm
from .models import Student, ID_photo, RegistrationForms, Class, Agent, Terms
from django.utils import timezone
from django.db import IntegrityError
from django.urls import reverse
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Prefetch, Q
from urllib.parse import urlencode
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def validate_agent_code(request):
    agent_code = request.GET.get('agent_code', None).lower()
    data = {
        'valid': Agent.objects.filter(agent_code__iexact=agent_code).exists()
    }
    return JsonResponse(data)

@csrf_exempt
def register_student(request, agent_code=None):
    if request.method == 'POST':
        step1_form = Step1Form(request.POST)
        step2_form = Step2Form(request.POST)
        step3_form = Step3Form(request.POST)
        id_card_upload_form = IdCardUploadForm(request.POST, request.FILES)

        if step1_form.is_valid() and step2_form.is_valid() and step3_form.is_valid() and id_card_upload_form.is_valid():
            print("Step1Form cleaned data:", step1_form.cleaned_data)

            # Create student instance but don't save yet
            student = step1_form.save(commit=False)
            student.agent = step1_form.cleaned_data.get('agent')
            student.registration_form = step1_form.cleaned_data.get('registration_form')
            student.terms_acknowledgment = step1_form.cleaned_data.get('terms_acknowledgment')

            print("Student instance before updating:", student.__dict__)

            # Assign student instance to Step2Form and Step3Form
            step2_form.instance = student
            step3_form.instance = student

            # Update student fields with Step2Form data
            for field, value in step2_form.cleaned_data.items():
                setattr(student, field, value)

            # Update student fields with Step3Form data
            for field, value in step3_form.cleaned_data.items():
                setattr(student, field, value)

            # Now save the student instance with all fields populated
            student.save()
            print("Student instance after saving:", student.__dict__)

            # Assign class IDs after saving
            student.class_id.set(step1_form.cleaned_data['class_id'])
            print("Student classes after saving:", student.class_id.all())

            # Save uploaded images
            for image_field in ['image1', 'image2', 'image3', 'image4']:
                image = id_card_upload_form.cleaned_data.get(image_field)
                if image:
                    ID_photo.objects.create(student=student, image=image)

            return redirect('registration_success', student_id=student.id)

    else:
        step1_form = Step1Form(initial={'display_agent': agent_code})
        step2_form = Step2Form()
        step3_form = Step3Form()
        id_card_upload_form = IdCardUploadForm()

    return render(request, 'register_student.html', {
        'step1_form': step1_form,
        'step2_form': step2_form,
        'step3_form': step3_form,
        'id_card_upload_form': id_card_upload_form,
        'agent_code': agent_code,  # Pass agent_code to the context
    })

@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        form = IdCardUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Get the first non-empty image field
            image = form.cleaned_data.get('image1') or form.cleaned_data.get('image2') or form.cleaned_data.get('image3') or form.cleaned_data.get('image4')

            if not image:
                return JsonResponse({'success': False, 'error': 'No image uploaded'}, status=400)

            # Open the image using Pillow
            img = Image.open(image)

            # Rotate if portrait
            if img.height > img.width:
                img = img.rotate(90, expand=True)

            # Resize with aspect ratio
            max_size = 800
            aspect_ratio = img.width / img.height
            new_width = max_size if img.width > img.height else int(max_size * aspect_ratio)
            new_height = int(new_width / aspect_ratio)

            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Save to BytesIO
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=60)
            img_io.seek(0)  # Reset pointer before using it

            # Convert to InMemoryUploadedFile
            img_file = InMemoryUploadedFile(
                img_io, None, image.name, 'image/jpeg', img_io.tell(), None
            )

            # Save to database
            image_instance = ID_photo.objects.create(image=img_file)

            return JsonResponse({'success': True, 'image_url': image_instance.image.url})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def registration_success(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    print(f"Student ID: {student.id}, Name: {student.name}, Email: {student.email}, Phone: {student.phone_numbers}, Address: {student.address}")
    return render(request, 'student_registration_success.html', {
        'student': student,
        'agent_code': student.agent.agent_code,  # Pass agent_code to the context
        'class_type': student.class_id.first().class_type 
    })

def student_registration_success(request, agent_code=None):
    return render(request, 'student_registration_success.html', {'agent_code': agent_code})


@require_GET
def get_registration_forms(request):
    class_ids = request.GET.getlist('class_id[]')  # Get list of selected class IDs
    print("Received class IDs:", class_ids)  # Debugging output

    if not class_ids:  # Handle case where no class is selected
        return JsonResponse({"registration_forms": []})

    # Fetch registration forms that are linked to the selected classes
    registration_forms = RegistrationForms.objects.filter(classes__id__in=class_ids).distinct()

    # Serialize data into a list of dictionaries
    data = [{"id": form.id, "name": form.name} for form in registration_forms]

    return JsonResponse({"registration_forms": data})

def get_terms(request):
    registration_form_id = request.GET.get('form_id')
    terms = Terms.objects.filter(form_id_id=registration_form_id)

    terms_data = [{'id': term.id, 'content': term.description} for term in terms]

    terms_data = [{'id': term.id, 'content': term.description} for term in terms]
    return JsonResponse({'terms': terms_data})

def dashboard(request):
    students = Student.objects.all().prefetch_related(
        Prefetch('class_id', queryset=Class.objects.all())
    )
    # Print the data being populated
    for student in students:
        print(f"Student ID: {student.id}, Name: {student.name}")
        for class_obj in student.class_id.all():
            print(f"  Class Type: {class_obj.class_type}")
            for form in class_obj.forms.all():
                print(f"    Registration Form: {form.name}")
    return render(request, 'dashboard.html', {'students': students})


def student_details(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'student_details.html', {'student': student})

class StudentList(APIView):
    def get(self, request):
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

class ClassList(APIView):
    def get(self, request):
        classes = Class.objects.all()
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)


def validate_id_no(request):
    id_no = request.GET.get('id_no', None)
    data = {
        'exists': Student.objects.filter(id_no=id_no).exists()
    }
    return JsonResponse(data)

@require_GET
def filter_students(request):
    id_no = request.GET.get('id_no', '').lower()
    name = request.GET.get('name', '').lower()
    agent_code = request.GET.get('agent_code', '').lower()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    students = Student.objects.all()

    if id_no:
        students = students.filter(id_no__icontains=id_no)
    if name:
        students = students.filter(name__icontains=name)
    if agent_code:
        students = students.filter(agent__agent_code__icontains=agent_code)
    if date_from:
        students = students.filter(registration_date__gte=date_from)
    if date_to:
        date_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        students = students.filter(registration_date__lt=date_to)

    students_data = []
    for counter, student in enumerate(students, 1):
        students_data.append({
            'counter': counter,
            'name': student.name,
            'id_no': student.id_no,
            'class_types': [class_obj.class_type for class_obj in student.class_id.all()],
            'registration_form': student.registration_form.name,
            'agent_code': student.agent.agent_code,
            'agent_name': student.agent.agent_name,
            'registration_date': student.registration_date.strftime("%d/%m/%Y %H:%M %p"),
            'id': student.id,
        })

    return JsonResponse({'students': students_data})
