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