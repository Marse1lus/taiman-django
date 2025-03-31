from rest_framework.permissions import BasePermission
from rest_framework import permissions
from .models import Project, Task

class IsExecutorOrAuthorOrReadOnly(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Автор может делать любые изменения
        if obj.author == request.user:
            return True
            
        # Исполнитель может менять только статус и добавлять комментарии
        if obj.executor == request.user:
            if request.method in ['PUT', 'PATCH']:
                # Проверяем, что в запросе есть только разрешенные поля
                allowed_fields = {'status', 'comment'}
                request_fields = set(request.data.keys())
                if not request_fields.issubset(allowed_fields):
                    return False
                return True
            return False
            
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return bool(request.user and request.user.is_staff)
    
class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
       
        if obj.user == request.user:
            return True
        
        if obj.executor == request.user:
            if request.method in ['PUT', 'PATCH']:
                if set(request.data.keys()) - {'status', 'comment'}:
                    return False 
                return True
            
            return False
        
        return False

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        
        try:
            project = Project.objects.get(id=project_id)
            return project.author == request.user or project.executor == request.user
        except Project.DoesNotExist:
            return False
        

class CanAddCommentToProject(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False
        
        try:
            project = Project.objects.get(id=project_id)
       
            return (project.author == request.user or 
                   project.executor == request.user or 
                   request.user.groups.filter(name='Avtor').exists())
        except Project.DoesNotExist:
            return False
