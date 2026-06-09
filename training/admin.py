from django.contrib import admin
from .models import Case, KnowledgeDocument, QuizSet, Question


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'problem_description')
    readonly_fields = ('created_at',)


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'is_processed', 'uploaded_at')
    list_filter = ('is_processed',)
    search_fields = ('title', 'description')
    readonly_fields = ('uploaded_at', 'is_processed', 'processed_at')


@admin.register(QuizSet)
class QuizSetAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz_set', 'created_by', 'created_at')
    list_filter = ('quiz_set',)
    search_fields = ('question_text',)
    readonly_fields = ('created_at',)
