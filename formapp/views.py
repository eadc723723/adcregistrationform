import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime

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
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

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

def preview_students(request):
    context = {'students': [], 'start_date': '', 'end_date': ''}

    if request.method == 'POST':
        try:
            start_date = request.POST.get('start_date', '')
            end_date = request.POST.get('end_date', '')

            if start_date and end_date:
                start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

                students = Student.objects.filter(
                    registration_date__range=(start_date_dt, end_date_dt)
                )

                context.update({
                    'students': students,
                    'message': 'Students fetched successfully',
                    'start_date': start_date,  # Retain the start date
                    'end_date': end_date,  # Retain the end date
                })
            else:
                context['error'] = 'Please provide both start and end dates.'
        except Exception as e:
            context['error'] = f'Error fetching students: {str(e)}'

    return render(request, 'delete_students.html', context)

def delete_students_by_date(request):
    context = {'students': [], 'start_date': '', 'end_date': ''}

    if request.method == 'POST':
        try:
            start_date = request.POST.get('start_date', '')
            end_date = request.POST.get('end_date', '')

            if start_date and end_date:
                start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

                students = Student.objects.filter(
                    registration_date__range=(start_date_dt, end_date_dt)
                )
                
                for student in students:
                    # Delete associated media files
                    for id_photo in student.id_photo_set.all():

                        if id_photo.image:
                            # Construct the file path and delete the file
                            file_path = id_photo.image.path
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                    deleted_count, _ = students.delete()


                # Retain the date values after deletion
                context.update({
                    'message': f'Successfully deleted {deleted_count} students.',
                    'start_date': start_date,
                    'end_date': end_date,
                })
            else:
                context['error'] = 'Please provide both start and end dates.'
        except Exception as e:
            context['error'] = f'Error deleting students: {str(e)}'

    return render(request, 'delete_students.html', context)


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

def preview_student_by_id(request):
    if request.method == 'GET':
        id_no = request.GET.get('id_no', '')
        
        if not id_no:
            return JsonResponse({'error': 'Please provide a student ID'}, status=400)
        
        try:
            student = Student.objects.get(id_no=id_no)
            return JsonResponse({
                'student': {
                    'id': student.id,
                    'name': student.name,
                    'registration_date': str(student.registration_date)
                }
            })
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student with this ID does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def delete_student_by_id(request):
    context = {'students': [], 'start_date': '', 'end_date': ''}
    
    if request.method == 'POST':
        try:
            id_no = request.POST.get('id_no', '')
            
            if id_no:
                try:
                    student = Student.objects.get(id_no=id_no)
                    # Delete associated media files
                    for id_photo in student.id_photo_set.all():  # Changed from id_photos to id_photo_set
                        if id_photo.image and os.path.isfile(id_photo.image.path):
                            os.remove(id_photo.image.path)
                    student.delete()
                    context.update({
                        'message': 'Student successfully deleted',
                        'start_date': request.POST.get('start_date', ''),
                        'end_date': request.POST.get('end_date', '')
                    })
                except Student.DoesNotExist:
                    context.update({
                        'error': 'Student with this ID does not exist',
                        'start_date': request.POST.get('start_date', ''),
                        'end_date': request.POST.get('end_date', '')
                    })
        except Exception as e:
            context.update({
                'error': f'Error deleting student: {str(e)}',
                'start_date': request.POST.get('start_date', ''),
                'end_date': request.POST.get('end_date', '')
            })
    
    return render(request, 'delete_students.html', context)

def agent_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('agent_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'agent_login.html', {'form': form})

@login_required
def agent_dashboard(request):
    agent_code = request.user.username

    # Check if any search parameters are provided
    search_performed = any([
        request.GET.get('student_id'),
        request.GET.get('student_name'),
        request.GET.get('date_from'),
        request.GET.get('date_to')
    ])

    students = Student.objects.none()  # Default: Don't load any data

    if search_performed:
        students = Student.objects.filter(agent__agent_code=agent_code)

        student_id = request.GET.get('student_id')
        student_name = request.GET.get('student_name')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')

        if student_id and student_id != 'null':
            students = students.filter(id__icontains=student_id)
        if student_name and student_name != 'null':
            students = students.filter(name__icontains=student_name)
        if date_from and date_from != 'null':
            students = students.filter(registration_date__gte=date_from)
        if date_to and date_to != 'null':
            date_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            students = students.filter(registration_date__lt=date_to)

    return render(request, 'agent_dashboard.html', {'students': students, 'search_performed': search_performed})

@login_required
def agent_student_details(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        student.id_no = request.POST.get('id_no')
        student.name = request.POST.get('name')
        student.gender = request.POST.get('gender')
        student.phone_numbers = request.POST.get('phone_numbers')
        student.address = request.POST.get('address')
        student.email = request.POST.get('email')
        student.contact_no_emergency = request.POST.get('contact_no_emergency')
        student.emergency_contact_relationship = request.POST.get('emergency_contact_relationship')
        student.save()
        messages.success(request, 'Student details updated successfully.')
        return redirect('agent_student_details', student_id=student.id)

    return render(request, 'agent_student_details.html', {'student': student})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password was successfully updated! Logging out...')
            logout(request)  # Logs the user out
            return redirect('/accounts/login/?password_changed=1')  # Redirect to login page with a flag
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'change_password.html', {'form': form})