from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class RegistrationForms(models.Model):
    name = models.CharField(max_length=255)
    classes = models.ManyToManyField('Class', blank=True)  # Make this field not required

    def __str__(self):
        return self.name
    

class Student(models.Model):
    name = models.CharField(max_length=255)
    id_no = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    gender = models.CharField(
        max_length=10, choices=[("male", "Male"), ("female", "Female")]
    )
    phone_numbers = models.CharField(
        max_length=255,
        blank=True,
    )
    email = models.EmailField(validators=[EmailValidator])
    contact_no_emergency = models.CharField(
        max_length=20,
    )
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    agent = models.ForeignKey("Agent", on_delete=models.SET_NULL, null=True, blank=False)
    registration_form = models.ForeignKey(
        "RegistrationForms", on_delete=models.CASCADE
    )
    class_id = models.ManyToManyField('Class', blank=True)
    registration_date = models.DateTimeField(default=timezone.now) 
    id_photos = models.ManyToManyField('Photo')
    

class Class(models.Model):
    class_type = models.CharField(max_length=100)
    forms = models.ManyToManyField('RegistrationForms', blank=True)

    def __str__(self):
        return self.class_type
    

class ID_photo(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='id_photos/')

    def save(self, *args, **kwargs):
        # Open the image using Pillow
        img = Image.open(self.image)

        # Convert the image to RGB mode if it has an alpha channel
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Rotate the image if it is in portrait mode
        if img.height > img.width:
            img = img.rotate(90, expand=True)

        # Calculate the new dimensions while maintaining the aspect ratio
        max_size = 800
        if img.width > img.height:
            new_width = max_size
            new_height = int((max_size / img.width) * img.height)
        else:
            new_height = max_size
            new_width = int((max_size / img.height) * img.width)

        # Resize the image
        img = img.resize((new_width, new_height), Image.LANCZOS)

        # Save the image to a BytesIO object
        img_io = BytesIO()
        img.save(img_io, format='JPEG', quality=60)

        # Create a new InMemoryUploadedFile
        img_file = InMemoryUploadedFile(img_io, None, self.image.name, 'image/jpeg', img_io.tell, None)

        # Set the image field to the new file
        self.image = img_file

        super().save(*args, **kwargs)

class Agent(models.Model):
    agent_code = models.CharField(max_length=20, unique=True)
    agent_name = models.CharField(max_length=255)
    def __str__(self):
        return self.agent_name

class Terms(models.Model):
    description = models.TextField()
    form_id = models.ForeignKey("RegistrationForms", on_delete=models.CASCADE)

class Photo(models.Model):
    url = models.URLField()
