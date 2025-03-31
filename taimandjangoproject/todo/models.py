from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Comment(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='project_comments', null=True, blank=True)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='task_comments', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.project:
            return f'Комментарий к проекту {self.project.title}'
        return f'Комментарий к задаче {self.task.title}'









class Todo(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    cat = models.ForeignKey('Category', on_delete=models.PROTECT, null=True)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    
    def __str__(self):
        return self.name 
    
    class Meta:
        verbose_name = 'GRC'
        verbose_name_plural = 'WRS'
        
class Project(models.Model):
    STATUS_CHOICES = [
        (1, 'Открыто'),
        (2, 'В работе'),
        (3, 'Исполнено'),
        (4, 'Закрыто'),
    ]

    title = models.CharField(max_length=255, verbose_name="Название проекта")
    description = models.TextField(verbose_name="Описание")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания", null=True, blank=True)
    executor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='executing_projects', verbose_name="Исполнитель")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_projects', verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comment = models.TextField(max_length=300, verbose_name="Комментарий")
    image = models.ImageField(upload_to='project_images/', null=True, blank=True,)


    def __str__(self):
        return self.title


class Task(models.Model):
    STATUS_CHOICES = [
        (1, 'Открыто'),
        (2, 'В работе'),
        (3, 'Исполнено'),
        (4, 'Закрыто')
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    number = models.IntegerField(verbose_name="Номер задачи")
    title = models.CharField(max_length=255, verbose_name="Название задачи")
    description = models.TextField(verbose_name="Описание задачи")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")

    class Meta:
        ordering = ['number']
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return f"Задача {self.number} - {self.title}"
    

class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='task_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)

    def __str__(self):
        return f"Файл {self.filename} для задачи {self.task.title}"
        
        