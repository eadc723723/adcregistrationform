from rest_framework import serializers
from .models import Student, Class

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'class_type']

class StudentSerializer(serializers.ModelSerializer):
    classes = ClassSerializer(source='class_id', many=True, read_only=True)
    
    class Meta:
        model = Student
        fields = ['id_no', 'name', 'classes']
