from rest_framework import serializers
from .models import Todo, Category, Project, Task, Comment, TaskFile
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response 
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User


class TodoModel:
    def __init__(self, title, content, cat):
        self.title = title
        self.content = content
        self.cat = cat

class TodoSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Todo
        fields = ['id', 'title', 'content', 'time_create', 'time_update', 'is_published', 'cat', 'user']

    def create(self, validated_data):
        return Todo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.content = validated_data.get("content", instance.content)
        instance.time_update = validated_data.get("time_update", instance.time_update)
        instance.is_published = validated_data.get("is_published", instance.is_published)
        instance.cat_id = validated_data.get("cat_id", instance.cat_id)
        instance.save()
        return instance

  

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'created_at', 'project', 'task']
        read_only_fields = ['author', 'project', 'task']

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')

class ProjectSerializer(serializers.ModelSerializer):
    executor = UserDetailSerializer(read_only=True)
    author = UserDetailSerializer(read_only=True)
    comments = CommentSerializer(source='project_comments', many=True, read_only=True)
    
    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError("Дата окончания не может быть раньше даты начала")
        return data

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'status', 'start_date', 
                 'end_date', 'executor', 'author', 'image', 
                 'created_at', 'comments']
        read_only_fields = ['author']  

class TaskFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskFile
        fields = ['id', 'file', 'uploaded_at', 'uploaded_by', 'filename']
        read_only_fields = ['uploaded_by']

class TaskSerializer(serializers.ModelSerializer):
    files = TaskFileSerializer(many=True, read_only=True)
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    comments = CommentSerializer(source='task_comments', many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'number', 'title', 'description', 'status', 
                 'start_date', 'end_date', 'files', 'project_id', 
                 'project_title', 'comments']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user