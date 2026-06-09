from django.contrib import admin
from .models import Case, KnowledgeDocument, QuizSet, Question, QuizAttempt
from .forms import QuizSetForm, QuestionForm


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
    form = QuizSetForm
    list_display = ('title', 'created_by', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at', 'created_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm
    list_display = ('question_text', 'quiz_set', 'created_by', 'created_at')
    list_filter = ('quiz_set',)
    search_fields = ('question_text',)
    readonly_fields = ('created_at', 'created_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuizAttempt)
class QuizAttemptRegister(admin.ModelAdmin):
    list_display = ('user', 'quiz_set', 'score', 'total_questions', 'passed', 'completed_at')
    list_filter = ('user', 'quiz_set')
    search_fields = ('user__username',)
    readonly_fields = ('completed_at',)