from django.db import models
from django.conf import settings

class Case(models.Model):
    title = models.CharField(max_length=255)
    problem_description = models.TextField()
    context = models.TextField()
    resolution = models.TextField()
    departments = models.JSONField(default=list)
    customer = models.ForeignKey(
        'database.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cases_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
class KnowledgeDocument(models.Model):
    file = models.FileField(upload_to='documents/' )
    title = models.CharField(max_length=255)
    keywords = models.JSONField(default=list)
    departments = models.JSONField(default=list)
    description = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.SET_NULL,
        null=True,
        related_name='documents_uploaded'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta: 
        verbose_name = 'Knowledge Document'
        verbose_name_plural = 'Knowledge Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title
    
class QuizSet(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    departments = models.JSONField(default=list)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='quiz_sets_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Quiz Set'
        verbose_name_plural = 'Quiz Sets'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
class Question(models.Model):
    question_text = models.TextField()
    correct_answer = models.TextField()
    source = models.TextField(blank=True)
    quiz_set = models.ForeignKey(
        QuizSet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions'
    )
    departments = models.JSONField(default=list)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='questions_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['-created_at']

    def __str__(self):
        return self.question_text[:80]