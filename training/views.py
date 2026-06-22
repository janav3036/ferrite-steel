from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from pgvector.django import CosineDistance
from .models import Case, QuizSet, QuizAttempt, KnowledgeDocument, DocumentChunk, Question, QuestionAttempt
from .forms import CaseForm, KnowledgeDocumentForm, QuizSetForm, QuestionForm
from .services.llm import judge_quiz_answer
from .services.processor import process_document
from aegis.notifications import notify
from aegis.models import CustomUser

PASS_THRESHOLD = 0.70


@login_required
def training_home(request):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    user = request.user
    if user.is_superuser or user.role == 'admin':
        case_count = Case.objects.count()
        quiz_count = QuizSet.objects.count()
    elif user.team:
        case_count = Case.objects.filter(departments__contains=user.team).count()
        quiz_count = sum(
            1 for qs in QuizSet.objects.all()
            if not qs.departments or user.team in qs.departments
        )
    else:
        case_count = 0
        quiz_count = 0
    return render(request, 'training/home.html', {
        'case_count': case_count,
        'quiz_count': quiz_count,
    })


@login_required
def case_list(request):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have permission to view cases.')
        return redirect('dashboard')
    user = request.user
    if user.is_superuser or user.role == 'admin':
        cases = Case.objects.select_related('customer', 'created_by').all()
    elif user.team:
        cases = Case.objects.select_related('customer', 'created_by').filter(
            departments__contains=user.team
        )
    else:
        cases = Case.objects.none()
    return render(request, 'training/case_list.html', {'cases': cases})


@login_required
def case_detail(request, pk):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to cases.')
        return redirect('dashboard')
    case = get_object_or_404(Case, pk=pk)
    user = request.user
    if not user.is_superuser and user.role != 'admin':
        if user.team not in (case.departments or []):
            messages.error(request, 'You do not have access to this case.')
            return redirect('case_list')
    return render(request, 'training/case_detail.html', {'case': case})


@login_required
def case_create(request):
    if not request.user.has_perm('training.add_case'):
        messages.error(request, 'You do not have permission to create cases.')
        return redirect('case_list')
    initial = {}
    notes = request.GET.get('notes', '')
    lead_pk = request.GET.get('lead', '')
    if notes:
        initial['problem_description'] = notes
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.departments = form.cleaned_data['departments']
            case.save()
            messages.success(request, 'Case created.')
            depts = form.cleaned_data.get('departments', [])
            if depts:
                recipients = CustomUser.objects.filter(team__in=depts, is_active=True).exclude(pk=request.user.pk)
            else:
                recipients = CustomUser.objects.filter(is_active=True).exclude(pk=request.user.pk)
            notify(recipients, f'New case: {case.title}',
                   message=f'Added by {request.user.get_full_name() or request.user.username}.',
                   link=f'/training/cases/{case.pk}/', notif_type='case_created')
            return redirect('case_detail', pk=case.pk)
    else:
        form = CaseForm(initial=initial)
    return render(request, 'training/case_create.html', {
        'form': form,
        'lead_pk': lead_pk,
    })


@login_required
def case_edit(request, pk):
    if not request.user.has_perm('training.change_case'):
        messages.error(request, 'You do not have permission to edit cases.')
        return redirect('case_list')
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.departments = form.cleaned_data['departments']
            obj.save()
            messages.success(request, 'Case updated.')
            return redirect('case_detail', pk=case.pk)
    else:
        form = CaseForm(instance=case, initial={'departments': case.departments})
    return render(request, 'training/case_edit.html', {'form': form, 'case': case})


@login_required
def case_delete(request, pk):
    if not request.user.has_perm('training.delete_case'):
        messages.error(request, 'You do not have permission to delete cases.')
        return redirect('case_list')
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        case.delete()
        messages.success(request, 'Case deleted.')
        return redirect('case_list')
    return render(request, 'training/case_confirm_delete.html', {'case': case})


@login_required
def quiz_list(request):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    user = request.user
    is_admin = user.is_superuser or user.role == 'admin'

    all_sets = QuizSet.objects.annotate(question_count=Count('questions')).order_by('-created_at')
    if not is_admin:
        all_sets = [qs for qs in all_sets if not qs.departments or user.team in qs.departments]

    if is_admin:
        quiz_set_data = []
        for qs in all_sets:
            attempts = QuizAttempt.objects.filter(quiz_set=qs)
            total = attempts.count()
            quiz_set_data.append({
                'quiz_set': qs,
                'total_attempts': total,
                'unique_takers': attempts.values('user').distinct().count(),
                'pass_count': attempts.filter(passed=True).count(),
            })

        standalone_qs = Question.objects.filter(quiz_set__isnull=True).annotate(
            attempt_count=Count('attempts'),
            correct_count=Count('attempts', filter=Q(attempts__correct=True)),
        ).order_by('created_at')
        return render(request, 'training/quiz_list.html', {
            'quiz_set_data': quiz_set_data,
            'standalone_questions': list(standalone_qs),
            'is_admin': True,
        })

    best_attempts = {}
    for attempt in QuizAttempt.objects.filter(user=user).select_related('quiz_set'):
        qid = attempt.quiz_set_id
        if qid is None:
            continue
        if qid not in best_attempts or attempt.score > best_attempts[qid].score:
            best_attempts[qid] = attempt

    quiz_set_data = []
    for qs in all_sets:
        best = best_attempts.get(qs.pk)
        quiz_set_data.append({
            'quiz_set': qs,
            'best_attempt': best,
            'passed': best.passed if best else False,
        })

    standalone_qs = Question.objects.filter(quiz_set__isnull=True).order_by('created_at')
    if user.team:
        standalone_qs = standalone_qs.filter(departments__contains=user.team)
    standalone_questions = list(standalone_qs)

    return render(request, 'training/quiz_list.html', {
        'quiz_set_data': quiz_set_data,
        'standalone_questions': standalone_questions,
        'is_admin': False,
    })


@login_required
def quiz_detail(request, pk):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    user = request.user
    if not (user.is_superuser or user.role == 'admin'):
        if quiz_set.departments and user.team not in quiz_set.departments:
            messages.error(request, 'You do not have access to this quiz.')
            return redirect('quiz_list')
    questions = quiz_set.questions.all()
    attempts = QuizAttempt.objects.filter(user=user, quiz_set=quiz_set).order_by('-completed_at')
    return render(request, 'training/quiz_detail.html', {
        'quiz_set': quiz_set,
        'questions': questions,
        'attempts': attempts,
        'pass_threshold': int(PASS_THRESHOLD * 100),
    })


@login_required
def quiz_take(request, pk):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    user = request.user
    if not (user.is_superuser or user.role == 'admin'):
        if quiz_set.departments and user.team not in quiz_set.departments:
            messages.error(request, 'You do not have access to this quiz.')
            return redirect('quiz_list')
    questions = list(quiz_set.questions.all())
    if not questions:
        messages.warning(request, 'This quiz has no questions yet.')
        return redirect('quiz_detail', pk=pk)

    if request.method == 'POST':
        results = []
        correct_count = 0
        for q in questions:
            user_answer = request.POST.get(f'answer_{q.pk}', '').strip()
            if user_answer:
                verdict = judge_quiz_answer(q.question_text, q.correct_answer, user_answer)
            else:
                verdict = {'correct': False, 'explanation': 'No answer provided.'}
            if verdict['correct']:
                correct_count += 1
            results.append({
                'question': q.question_text,
                'user_answer': user_answer,
                'correct': verdict['correct'],
                'explanation': verdict['explanation'],
            })

        total = len(questions)
        passed = (correct_count / total) >= PASS_THRESHOLD if total > 0 else False

        attempt = QuizAttempt.objects.create(
            user=user,
            quiz_set=quiz_set,
            score=correct_count,
            total_questions=total,
            passed=passed,
        )
        request.session[f'quiz_results_{attempt.pk}'] = results
        return redirect('quiz_results', pk=attempt.pk)

    return render(request, 'training/quiz_take.html', {
        'quiz_set': quiz_set,
        'questions': questions,
    })


@login_required
def quiz_results(request, pk):
    attempt = get_object_or_404(QuizAttempt, pk=pk, user=request.user)
    results = request.session.pop(f'quiz_results_{attempt.pk}', [])
    return render(request, 'training/quiz_results.html', {
        'attempt': attempt,
        'results': results,
        'pass_threshold': int(PASS_THRESHOLD * 100),
    })


@login_required
def question_practice(request, pk):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    question = get_object_or_404(Question, pk=pk, quiz_set__isnull=True)
    user = request.user
    if not (user.is_superuser or user.role == 'admin'):
        if question.departments and user.team not in question.departments:
            messages.error(request, 'You do not have access to this question.')
            return redirect('quiz_list')
    verdict = None
    user_answer = ''
    if request.method == 'POST':
        user_answer = request.POST.get('user_answer', '').strip()
        if user_answer:
            verdict = judge_quiz_answer(question.question_text, question.correct_answer, user_answer)
            QuestionAttempt.objects.create(
                user=request.user,
                question=question,
                user_answer=user_answer,
                correct=verdict['correct'],
            )
        else:
            verdict = {'correct': False, 'explanation': 'No answer provided.'}
    return render(request, 'training/question_practice.html', {
        'question': question,
        'user_answer': user_answer,
        'verdict': verdict,
    })


@login_required
def quiz_set_attempts(request, pk):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return redirect('quiz_list')
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    attempts = QuizAttempt.objects.filter(quiz_set=quiz_set).select_related('user').order_by('-completed_at')
    return render(request, 'training/quiz_set_attempts.html', {
        'quiz_set': quiz_set,
        'attempts': attempts,
    })


@login_required
def question_attempts(request, pk):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return redirect('quiz_list')
    question = get_object_or_404(Question, pk=pk, quiz_set__isnull=True)
    attempts = QuestionAttempt.objects.filter(question=question).select_related('user').order_by('-attempted_at')
    return render(request, 'training/question_attempts.html', {
        'question': question,
        'attempts': attempts,
    })


@login_required
def document_list(request):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    user = request.user
    if user.is_superuser or user.role == 'admin':
        docs = KnowledgeDocument.objects.all()
    elif user.team:
        docs = KnowledgeDocument.objects.filter(departments__contains=user.team)
    else:
        docs = KnowledgeDocument.objects.none()
    return render(request, 'training/document_list.html', {'docs': docs})


@login_required
def document_detail(request, pk):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    doc = get_object_or_404(KnowledgeDocument, pk=pk)
    chunk_count = doc.chunks.count()
    return render(request, 'training/document_detail.html', {'doc': doc, 'chunk_count': chunk_count})


@login_required
def document_delete(request, pk):
    if not request.user.has_perm('training.delete_case'):
        messages.error(request, 'You do not have permission to delete documents.')
        return redirect('document_list')
    doc = get_object_or_404(KnowledgeDocument, pk=pk)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, 'Document deleted.')
        return redirect('document_list')
    return render(request, 'training/document_confirm_delete.html', {'doc': doc})

@login_required
def document_create(request):
    if not request.user.has_perm('training.add_case'):
        messages.error(request, 'You do not have permission to add documents.')
        return redirect('document_list')
    if request.method == 'POST':
        form = KnowledgeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.departments = form.cleaned_data['departments']
            doc.save()
            if doc.source_type == 'file':
                file_obj = form.cleaned_data.get('file')
                if file_obj:
                    doc.filename = file_obj.name
                    doc.save(update_fields=['filename'])
            try:
                file_obj = form.cleaned_data.get('file')
                if doc.source_type == 'file' and file_obj:
                    process_document(doc, file_obj=file_obj, filename=file_obj.name)
                elif doc.source_type == 'text':
                    process_document(doc)
                else:
                    messages.warning(request, 'No file uploaded — document saved but not processed.')
                    return redirect('document_detail', pk=doc.pk)
                messages.success(request, 'Document processed successfully.')
            except Exception as e:
                messages.error(request, f'Processing failed: {e}')
            return redirect('document_detail', pk=doc.pk)
    else:
        form = KnowledgeDocumentForm()
    return render(request, 'training/document_create.html', {'form': form})


@login_required
def document_ask(request):
    if not request.user.has_perm('training.view_case'):
        messages.error(request, 'You do not have access to Training.')
        return redirect('dashboard')
    user = request.user

    if user.is_superuser or user.role == 'admin':
        avail_qs = KnowledgeDocument.objects.filter(is_processed=True)
    elif user.team:
        avail_qs = KnowledgeDocument.objects.filter(is_processed=True, departments__contains=user.team)
    else:
        avail_qs = KnowledgeDocument.objects.none()
    available_docs = list(avail_qs.values('id', 'title', 'filename'))

    answer = None
    question = ''
    selected_docs = []

    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        raw_ids = request.POST.getlist('doc_ids')
        selected_ids = [int(x) for x in raw_ids if x.isdigit()]
        if selected_ids:
            selected_docs = list(avail_qs.filter(id__in=selected_ids).values('id', 'title', 'filename'))

        if question:
            from .services.embedder import embed_query
            from .services.llm import answer_question
            try:
                query_embedding = embed_query(question)
                chunk_qs = DocumentChunk.objects.filter(document__is_processed=True)
                if selected_ids:
                    chunk_qs = chunk_qs.filter(document_id__in=selected_ids)
                elif not (user.is_superuser or user.role == 'admin') and user.team:
                    chunk_qs = chunk_qs.filter(document__departments__contains=user.team)
                chunks = list(chunk_qs.annotate(
                    distance=CosineDistance('embedding', query_embedding)
                ).order_by('distance')[:5])
                case_qs = Case.objects.all()
                if not (user.is_superuser or user.role == 'admin') and user.team:
                    case_qs = case_qs.filter(departments__contains=user.team)
                cases = list(case_qs.filter(
                    Q(title__icontains=question) |
                    Q(problem_description__icontains=question) |
                    Q(resolution__icontains=question)
                )[:3])
                question_qs = Question.objects.all()
                if not (user.is_superuser or user.role == 'admin') and user.team:
                    question_qs = question_qs.filter(departments__contains=user.team)
                quiz_questions = list(question_qs.filter(
                    Q(question_text__icontains=question) |
                    Q(correct_answer__icontains=question)
                )[:3])
                answer = answer_question(question, chunks, cases, quiz_questions)
            except Exception as e:
                messages.error(request, f'Could not get answer: {e}')
    import json as _json
    return render(request, 'training/document_ask.html', {
        'question': question,
        'answer': answer,
        'available_docs': available_docs,
        'selected_docs': selected_docs,
        'available_docs_json': _json.dumps(available_docs),
        'selected_docs_json': _json.dumps(selected_docs),
    })
@login_required
def question_list(request):
    if not request.user.has_perm('training.change_question'):
        messages.error(request, 'You do not have permission to manage questions.')
        return redirect('quiz_list')
    questions = Question.objects.select_related('quiz_set', 'created_by').order_by('quiz_set__title', 'created_at')
    return render(request, 'training/question_list.html', {'questions': questions})


@login_required
def quiz_set_create(request):
    if not request.user.has_perm('training.add_quizset'):
        messages.error(request, 'You do not have permission to create quiz sets.')
        return redirect('quiz_list')
    if request.method == 'POST':
        form = QuizSetForm(request.POST)
        if form.is_valid():
            qs = form.save(commit=False)
            qs.created_by = request.user
            qs.departments = form.cleaned_data['departments']
            qs.save()
            messages.success(request, 'Quiz set created.')
            return redirect('quiz_detail', pk=qs.pk)
    else:
        form = QuizSetForm()
    return render(request, 'training/quiz_set_create.html', {'form': form})


@login_required
def quiz_set_edit(request, pk):
    if not request.user.has_perm('training.change_quizset'):
        messages.error(request, 'You do not have permission to edit quiz sets.')
        return redirect('quiz_list')
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    if request.method == 'POST':
        form = QuizSetForm(request.POST, instance=quiz_set)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.departments = form.cleaned_data['departments']
            obj.save()
            messages.success(request, 'Quiz set updated.')
            return redirect('quiz_detail', pk=quiz_set.pk)
    else:
        form = QuizSetForm(instance=quiz_set, initial={'departments': quiz_set.departments})
    return render(request, 'training/quiz_set_edit.html', {'form': form, 'quiz_set': quiz_set})


@login_required
def quiz_set_delete(request, pk):
    if not request.user.has_perm('training.delete_quizset'):
        messages.error(request, 'You do not have permission to delete quiz sets.')
        return redirect('quiz_list')
    quiz_set = get_object_or_404(QuizSet, pk=pk)
    if request.method == 'POST':
        quiz_set.delete()
        messages.success(request, 'Quiz set deleted.')
        return redirect('quiz_list')
    return render(request, 'training/quiz_set_confirm_delete.html', {'quiz_set': quiz_set})

@login_required
def question_create(request, quiz_pk=None):
    if not request.user.has_perm('training.add_question'):
        messages.error(request, 'You do not have permission to create questions.')
        return redirect('quiz_list')
    initial = {}
    if quiz_pk:
        quiz_set = get_object_or_404(QuizSet, pk=quiz_pk)
        initial['quiz_set'] = quiz_set
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.created_by = request.user
            q.departments = form.cleaned_data['departments']
            q.save()
            messages.success(request, 'Question added.')
            if q.quiz_set:
                return redirect('quiz_detail', pk=q.quiz_set.pk)
            return redirect('quiz_list')
    else:
        form = QuestionForm(initial=initial)
    return render(request, 'training/question_create.html', {'form': form, 'quiz_pk': quiz_pk})


@login_required
def question_edit(request, pk):
    if not request.user.has_perm('training.change_question'):
        messages.error(request, 'You do not have permission to edit questions.')
        return redirect('quiz_list')
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.departments = form.cleaned_data['departments']
            obj.save()
            messages.success(request, 'Question updated.')
            if obj.quiz_set:
                return redirect('quiz_detail', pk=obj.quiz_set.pk)
            return redirect('quiz_list')
    else:
        form = QuestionForm(instance=question, initial={'departments': question.departments})
    return render(request, 'training/question_edit.html', {'form': form, 'question': question})


@login_required
def question_delete(request, pk):
    if not request.user.has_perm('training.delete_question'):
        messages.error(request, 'You do not have permission to delete questions.')
        return redirect('quiz_list')
    question = get_object_or_404(Question, pk=pk)
    quiz_pk = question.quiz_set.pk if question.quiz_set else None
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted.')
        if quiz_pk:
            return redirect('quiz_detail', pk=quiz_pk)
        return redirect('quiz_list')
    return render(request, 'training/question_confirm_delete.html', {'question': question})
