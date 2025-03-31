from rest_framework.views import APIView
from rest_framework.response import Response
from django.forms.models import model_to_dict
from rest_framework import generics
from .models import Todo
from .serializers import (
	TodoSerializer, 
	ProjectSerializer, 
	CommentSerializer,
	TaskFileSerializer,
	UserSerializer
)
from rest_framework import status
from rest_framework import viewsets 
from rest_framework.decorators import action
from .models import Category
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated ,IsAuthenticatedOrReadOnly 
from rest_framework.permissions import IsAdminUser
# from .permission import IsOwnerOrReadOnly 
from rest_framework.authentication import TokenAuthentication
from .models import Project, Task, Comment, TaskFile
from .serializers import TaskSerializer, ProjectSerializer, CommentSerializer
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.contrib.auth.models import User
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter
from .permission import IsExecutorOrAuthorOrReadOnly
from .permission import CanAddCommentToProject
from django.http import Http404, HttpResponseForbidden
from .serializers import CommentSerializer
from .models import Comment

def check_user_group(username):
	try:
		user=User.objects.get(username=username)
		groups = user.groups.values_list('name', flat=True)
		return list(groups)
	except User.DoesNotExist:
		return "Пользователь не найден"
	
def check_user_role(request, project):
	is_executor = project.executor == request.user
	is_author = project.author == request.user
	return {
		'is_executor': is_executor,
		'is_author': is_author,
		'is_admin': request.user.is_staff
	}

class ProjectFilter(filters.FilterSet):
	status = filters.CharFilter(field_name='status')
	start_date = filters.DateFilter(field_name='start_date')
	end_date = filters.DateFilter(field_name='end_date', lookup_expr='lte')

	class Meta:
		model = Project
		fields = ['status', 'start_date', 'end_date', 'executor']
		
class ProjectAPIList(APIView):
	parser_classes = (MultiPartParser, FormParser, JSONParser)
	permission_classes = (IsAuthenticated, IsExecutorOrAuthorOrReadOnly)

	def get_objects(self, pk):
		try:
			obj = Project.objects.get(pk=pk)
			self.check_objects_permission(self.request, obj)
			return obj
		except Project.DoesNotExist:
			raise Http404

	def get(self, request, pk=None):
		if pk:
			try:
				project = Project.objects.get(pk=pk)
				serializer = ProjectSerializer(project)
				return Response(serializer.data)
			except Project.DoesNotExist:
				return Response({"error": "Проект не найден ле"})
		projects = Project.objects.all()
		status = request.query_params.get('status')
		if status:
			projects = projects.filter(status=status)

		sort_by = request.query_params.get('sort')
		if sort_by:
			projects = projects.order_by(sort_by)
		else:
			projects = projects.order_by('-created_at')

		serializer = ProjectSerializer(projects, many=True)
		return Response(serializer.data)

	def post(self, request, pk=None):
		if pk:
			return Response({"error": "Method POST not allowed"})
		if not request.user.groups.filter(name='Avtor').exists():
			return Response(
				{"error": "Только авторы могут создавать проекты"}, 
				status=status.HTTP_403_FORBIDDEN
			)
		data = request.data.copy()
		data['author'] = request.user.id
		
		if 'executor' not in data:
			return Response(
				{"error": "Необходимо указать исполнителя (executor)"}, 
				status=status.HTTP_400_BAD_REQUEST
			)

		serializer = ProjectSerializer(data=data)
		if serializer.is_valid():
			project = serializer.save(
				author=request.user,
				executor_id=data['executor']
			)
			return Response(serializer.data, status=201)
		return Response(serializer.errors, status=400)

	def put(self, request, pk):
		try:
			project = Project.objects.get(id=pk)
			roles = check_user_role(request, project)
			
			if roles['is_executor']:
				if 'status' in request.data:
					project.status = request.data['status']
					project.save()
					serializer = ProjectSerializer(project)
					return Response(serializer.data)
				return Response(
					{"error": "Исполнитель может изменять только статус проекта"},
					status=status.HTTP_403_FORBIDDEN
				)
			elif roles['is_author']:
				serializer = ProjectSerializer(project, data=request.data, partial=True)
				if serializer.is_valid():
					serializer.save()
					return Response(serializer.data)
				return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response(
					{"error": "Только автор или исполнитель могут изменять проект"},
					status=status.HTTP_403_FORBIDDEN
				)
		except Project.DoesNotExist:
			return Response({"error": "Проект не найден"}, status=status.HTTP_404_NOT_FOUND)
		
	def delete(self, request, *args, **kwargs):
		pk = kwargs.get("pk", None)
		if not pk:
			return Response({"error": "Method DELETE not allowed"})
		try:
			instance = Project.objects.get(pk=pk)
			instance.delete()
			return Response({"message": "Проект удален"})
		except Project.DoesNotExist:
			return Response({"error": "Проект не найден"})
	
class TaskAPIView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request, project_id=None, task_id=None):
		if project_id and task_id:
			try:
				task = Task.objects.get(id=task_id, project_id=project_id)
				serializer = TaskSerializer(task)
				return Response(serializer.data)
			except Task.DoesNotExist:
				return Response({"error": "задача не найдена"}, status=status.HTTP_404_NOT_FOUND) 
		elif project_id:
			tasks = Task.objects.filter(project_id=project_id)
			serializer = TaskSerializer(tasks, many=True)
			return Response(serializer.data)
		else:
			tasks = Task.objects.all()
			serializer = TaskSerializer(tasks, many=True)
			return Response(serializer.data)
	
	def post(self, request, project_id=None):
		try:
			project = Project.objects.get(id=project_id)
			serializer = TaskSerializer(data=request.data)
			if serializer.is_valid():
				serializer.save(project=project)
				return Response(serializer.data, status=status.HTTP_201_CREATED)
			return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
		except Project.DoesNotExist:
			return Response({"error": "Проект не найден"}, status=status.HTTP_404_NOT_FOUND)

	def put(self, request, project_id, task_id):
		task = Task.objects.get(id=task_id, project_id=project_id)
		project = Project.objects.get(id=project_id)

		is_executor = project.executor == request.user
		is_author = project.author == request.user
		is_in_author_group = request.user.groups.filter(name='Avtor').exists()

		if is_author or is_in_author_group:
			serializer = TaskSerializer(task, data=request.data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data)
			return Response(serializer.errors, status=400)
		
		if is_executor and not is_author:
			if 'status' in request.data:
				task.status = request.data['status']
				task.save()
				return Response(TaskSerializer(task).data)
			return Response({"error": "Только статус можно менять"}, status=403)

		return Response({"error": "Нет прав"}, status=403)
	
	def delete(self, request, project_id, task_id):
		try:
			task = Task.objects.get(id=task_id, project=project_id)
			task.delete()
			return Response({"message": "Задача удалена"}, status=204)
		except Task.DoesNotExist:
			return Response(
				{"error": "Задача не найдена"},
				status=404
			)
		
class ProjectCommentView(APIView):
	parser_classes = (JSONParser, MultiPartParser, FormParser)
	permission_classes = (IsAuthenticated,)

	def get(self, request, project_id, comment_id=None):
		comments = Comment.objects.filter(project_id=project_id)
		serializer = CommentSerializer(comments,many=True)
		return Response(serializer.data) 
	
	def post(self, request, project_id):
		try:
			project = Project.objects.get(id=project_id)
			serializer = CommentSerializer(data=request.data)
			if serializer.is_valid():
				serializer.save(author=request.user, project=project)
				return Response(serializer.data, status=status.HTTP_201_CREATED)
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		except Project.DoesNotExist:
			return Response({"error": "Проект не найден"}, status=status.HTTP_404_NOT_FOUND)
		
	def put(self, request, project_id, comment_id):
		try:
			comment = Comment.objects.get(id=comment_id, project_id=project_id)
			if not (request.user == comment.author or request.user.groups.filter(name='Avtor').exists()):
				return Response ({"error": "Только автор комментария или автор проекта может вносить изменения"},
					 status=403
					 )
			
			serializer = CommentSerializer(data=request.data, instance=comment)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data)
			return Response(serializer.errors, status=400)
		except Comment.DoesNotExist:
			return Response({"error": "Комментарий не найден"}, status=status.HTTP_404_NOT_FOUND)

class TaskCommentView(APIView):
	parser_classes =(MultiPartParser,FormParser, JSONParser)
	permission_classes = (IsAuthenticated, IsAuthenticatedOrReadOnly, CanAddCommentToProject)

	def get(self, request, project_id, task_id):
		try:
			task = Task.objects.get(id=task_id, project_id=project_id)
			comments = Comment.objects.filter(task=task)
			serializer= CommentSerializer(comments, many=True)
			return Response(serializer.data)
		except Task.DoesNotExist:
			return Response({"error": "Задача не найдена ле"},status=status.HTTP_404_NOT_FOUND)
	
	def post(self, request, project_id, task_id):
		try:
			task = Task.objects.get(id=task_id, project_id=project_id)
			serializer = CommentSerializer(data=request.data)
			if serializer.is_valid():
				serializer.save(author=request.user, task=task)
				return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
		except Task.DoesNotExist:
			return Response ({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)

	def put(self, request, project_id, task_id, comment_id):
		try:
			task = Task.objects.get(id=task_id, project_id=project_id)
			comment = Comment.objects.get(id=comment_id, task=task)
			
			is_avtor = request.user.groups.filter(name='Avtor').exists()
			is_executor = task.project.executor == request.user

			if is_avtor:
				if comment.author == task.project.executor:
					return Response(
						{"error": "Автор проекта не может исправлять комментарий исполнителя"},
						status=403
					)
				
			serializer = CommentSerializer(comment, data=request.data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data)
			
			if is_executor and comment.author == request.user:
				serializer = CommentSerializer(comment, data=request.data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data)
			if is_executor:
				return Response(
					{"error": "Исполнитель может редактировать только свои комментарии"},
					status=403
				)
			
			return Response(
				{"error": "Только автор проекта или исполнитель задачи могут редактировать комментарии"},
				status=403
			)
		
		except Task.DoesNotExist:
			return Response({"error": "Задача не найдена"}, status=404)
		except Comment.DoesNotExist:
			return Response({"error":"Комментарий не найден"}, status=404)




class TaskFileView(APIView):
	parser_classes = (MultiPartParser, FormParser, JSONParser)
	permission_classes = (IsAuthenticatedOrReadOnly,)

	def get(self, request, project_id, task_id):
		try:
			task = Task.objects.get(id=task_id, project_id=project_id)
			files = task.files.all()
			serializer = TaskSerializer(files, many=True)
			return Response(serializer.data)
		except Task.DoesNotExist:
			return Response({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)

	def post(self, request, project_id, task_id):
		try:
			task = Task.objects.get(id=task_id, project_id=project_id)
			file_obj = request.FILES['file']
			
			task_file = TaskFile.objects.create(
				task=task,
				file=file_obj,
				filename=file_obj.name,
				uploaded_by=request.user
			)
			
			serializer = TaskFileSerializer(task_file)
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		except Task.DoesNotExist:
			return Response({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)
		except KeyError:
			return Response({"error": "Файл не предоставлен"}, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(APIView):
	def post(self, request):
		serializer = UserSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def project_update_view(request, project_id):
    project = Project.objects.get(id=project_id)
    

    if request.user.groups.filter(name='Исполнитель').exists():
    
        pass
    else:
        return HttpResponseForbidden("У вас нет прав для изменения этого проекта")

def check_user_group(username):
    try:
        user = User.objects.get(username=username)
        groups = user.groups.values_list('name', flat=True) 
        return list(groups)
    except User.DoesNotExist:
        return "Пользователь не найден"

user_groups = check_user_group('username')
print(user_groups)

def check_user_role(request, project):
    is_executor = project.executor == request.user
    is_author = project.author == request.user
    
    return {
        'is_executor': is_executor, 
        'is_author': is_author,
        'is_admin': request.user.is_staff
    }

class TodoAPIView(APIView):
	permission_classes = (IsAuthenticatedOrReadOnly,)

	def get(self, request, pk=None, *args, **kwargs):
		if pk:
			try:
				todo = Todo.objects.get(id=pk)
				serializer = TodoSerializer(todo)
				return Response(serializer.data)
			except Todo.DoesNotExist:
				return Response({"error": "Объект не найден"})
		else:
			todos = Todo.objects.all()
			serializer = TodoSerializer(todos, many=True)
			return Response(serializer.data)
	
	def post(self, request):
		serializer = TodoSerializer(data=request.data, context={'request': request})
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	def put(self, request, *args, **kwargs):
		pk = kwargs.get("pk", None)
		if not pk:
			return Response({"error": "Method PUT not allowed"})
		try:
			instance = Todo.objects.get(pk=pk)
			serializer = TodoSerializer(data=request.data, instance=instance, context={'request': request})
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data)
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		except Todo.DoesNotExist:
			return Response({"error": "Объект не найден"})
	
	def delete(self, request, *args, **kwargs):
		pk = kwargs.get("pk", None)
		if not pk:
			return Response({"error": "Method DELETE not allowed"})
		try:
			instance = Todo.objects.get(pk=pk)
			instance.delete()
			return Response({"message": "Todo успешно удален"})
		except Todo.DoesNotExist:
			return Response({"error": "Объект не найден"})


class TodoDetailAPIView(APIView):
	def get(self, request, pk):
		todos = Todo.objects.get(id=pk)
		serializer = TodoSerializer(todos)
		return Response(serializer.data)


	
	def post(self,request):
		post_new = Todo.objects.create(
			title=request.data['title'],
			content=request.data['content'],
			cat_id=request.data['cat']	
		)
		return Response({'post': model_to_dict(post_new)})
