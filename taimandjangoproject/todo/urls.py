from django.urls import path, re_path
from .views import  TodoAPIView, ProjectCommentView, TaskCommentView, TodoAPIView
from rest_framework import routers
from django.contrib import admin
from django.conf.urls import include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken import views
from .views import ProjectAPIList, ProjectCommentView, TaskAPIView
from .views import TaskFileView 
from .views import UserRegistrationView
router = routers.SimpleRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)), 
    path('api/v1/todolist/', TodoAPIView.as_view()),
	path('api/v1/todolist/<int:pk>/', TodoAPIView.as_view()),	
	path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/projects/<int:project_id>/comments/', ProjectCommentView.as_view(), name='project-comments'),
    path('auth/token/login/', views.obtain_auth_token),
	path('api/v1/projects/', ProjectAPIList.as_view(), name='project-list'),  # новый
    path('api/v1/projects/<int:pk>/', ProjectAPIList.as_view(), name='project-detail'),  # новый
    path('api/v1/projects/<int:project_id>/comments/<int:comment_id>/', ProjectCommentView.as_view(), name='project-comment-detail'),
	path('api/v1/projects/<int:project_id>/tasks/', TaskAPIView.as_view(), name='project-tasks'),
    path('api/v1/projects/<int:project_id>/tasks/<int:task_id>/', TaskAPIView.as_view(), name='project-task-detail'),
    path('api/v1/projects/<int:project_id>/tasks/<int:task_id>/comments/', TaskCommentView.as_view(), name='task-comments'),
    path('api/v1/projects/<int:project_id>/tasks/<int:task_id>/comments/<int:comment_id>/', TaskCommentView.as_view(), name='task-comment-detail'),
    path('api/v1/projects/<int:project_id>/tasks/<int:task_id>/files/', TaskFileView.as_view(), name='task-files'),
	path('api/v1/auth/register/', UserRegistrationView.as_view(), name='register'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 