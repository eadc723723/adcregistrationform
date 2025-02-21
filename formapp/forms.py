from django import forms
from .models import Student, ID_photo, RegistrationForms, Class, Agent, Terms

class IdCardUploadForm(forms.Form):
    image1 = forms.ImageField(required=False, widget=forms.FileInput(attrs={'id': 'id_card_form_image1'}))
    image2 = forms.ImageField(required=False, widget=forms.FileInput(attrs={'id': 'id_card_form_image2'}))
    image3 = forms.ImageField(required=False, widget=forms.FileInput(attrs={'id': 'id_card_form_image3'}))
    image4 = forms.ImageField(required=False, widget=forms.FileInput(attrs={'id': 'id_card_form_image4'}))

class Step1Form(forms.ModelForm):
    display_agent = forms.CharField(
        required=False,
        widget=forms.TextInput(),  # Removed 'readonly' attribute
    )
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.all(),
        widget=forms.HiddenInput(),
        required=False  # Hidden field to store the actual Agent instance
    )

    class_id = forms.ModelMultipleChoiceField(
        queryset=Class.objects.all(),  # Use the Class model directly
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'class-type-checkbox'}),  
    )
    registration_form = forms.ModelChoiceField(
        queryset=RegistrationForms.objects.none(),  # Initialize with an empty queryset
        widget=forms.RadioSelect(attrs={'class': 'registration-form-radio'}),
        required=True  # Ensure the field is required
    )
    terms_acknowledgment = forms.BooleanField(
        required=True,
        label='I acknowledge that I have read and agree to the terms and conditions.'
    )

    class Meta:
        model = Student
        fields = ['display_agent', 'agent', 'class_id', 'registration_form', 'terms_acknowledgment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'class_id' in self.data:
            class_ids = self.data.getlist('class_id')
            self.fields['registration_form'].queryset = RegistrationForms.objects.filter(classes__id__in=class_ids).distinct()
        elif self.instance.pk:
            self.fields['registration_form'].queryset = self.instance.class_id.registrationforms_set.all()

    def clean(self):
        cleaned_data = super().clean()
        display_agent = cleaned_data.get('display_agent')

        if display_agent:
            try:
                agent = Agent.objects.get(agent_code__iexact=display_agent)  # Ensure this matches actual field
                cleaned_data['agent'] = agent  # Store the actual Agent instance
            except Agent.DoesNotExist:
                self.add_error('display_agent', 'Agent does not exist.')

        return cleaned_data

class Step2Form(forms.ModelForm):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)

    def clean_id_no(self):
        id_no = self.cleaned_data.get('id_no')
        if Student.objects.filter(id_no=id_no).exists():
            raise forms.ValidationError("A student with this ID number already exists. Please use a different ID number.")
        return id_no

    def save(self, commit=True):
        self.clean_id_no()
        return super().save(commit=commit)

    class Meta:
        model = Student
        fields = ['name', 'id_no', 'address', 'gender']

class Step3Form(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['phone_numbers', 'email', 'contact_no_emergency', 'emergency_contact_relationship']

class RegistrationFormsForm(forms.ModelForm):
    class Meta:
        model = RegistrationForms
        fields = '__all__'

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = '__all__'

class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = '__all__'
