from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from forum.models import Article, Comment, Question, Answer
from forum.forms import ArticleForm, CommentForm, QuestionForm, AnswerForm
from django.urls import reverse
from django.db.models import Count

# View untuk menampilkan halaman utama (Culinary Insights)
def show_main(request):
    articles = Article.objects.all().order_by('-created_at')
    questions = Question.objects.annotate(total_answers=Count('answers')).order_by('-created_at')

    article_form = ArticleForm()
    question_form = QuestionForm()

    context = {
        'articles': articles,
        'questions': questions,
        'article_form': article_form,
        'question_form': question_form,
    }
    return render(request, 'culinary_insights.html', context)

# View untuk menampilkan detail artikel dan komentar
@login_required(login_url='/auth/login/') 
def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    comments = Comment.objects.filter(article=article)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('auth:login')

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
            return redirect('forum:article_detail', article_id=article.id)
    else:
        comment_form = CommentForm()

    context = {
        'article': article,
        'comments': comments,
        'comment_form': comment_form,
    }

    return render(request, 'article_detail.html', context)

# View untuk menambah artikel
@login_required(login_url='/auth/login/')
def add_article(request):
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.user = request.user
            article.save()
            return JsonResponse({
                'success': True,
                'article': {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'thumbnail_url': article.get_thumbnail() or '/static/image/default-thumbnail.jpg',
                    'url': reverse('forum:article_detail', args=[article.id]),
                }
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# View untuk mengedit artikel
@login_required(login_url='/auth/login/')
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    # Authorization check
    if request.user != article.user and not request.user.is_staff:
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

    # Handle GET request for editing the article (optional, only if you want to support it)
    if request.method == 'GET':
        form = ArticleForm(instance=article)
        return JsonResponse({
            "success": True,
            "form": {
                "title": article.title,
                "content": article.content,
                "thumbnail_url": article.thumbnail_url
            }
        })

    # Handle POST request for saving the edited article
    elif request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Article updated successfully"})
        else:
            return JsonResponse({
                "success": False,
                "message": "Invalid data",
                "errors": form.errors  # Send form validation errors to frontend
            }, status=400)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)

# View untuk menghapus artikel
def delete_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.user != article.user and not request.user.is_staff:
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

    article.delete()
    # Redirect ke halaman utama atau ke #section di halaman Culinary Insights
    return redirect(reverse('forum:show_main') + '#articles-section')

# View untuk menampilkan detail pertanyaan (QnA) dan jawaban
@login_required(login_url='/auth/login/') 
def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    answers = Answer.objects.filter(question=question)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('auth:login')

        answer_form = AnswerForm(request.POST)
        if answer_form.is_valid():
            answer = answer_form.save(commit=False)
            answer.question = question
            answer.user = request.user
            answer.save()
            return redirect('forum:question_detail', question_id=question.id)
    else:
        answer_form = AnswerForm()

    context = {
        'question': question,
        'answers': answers,
        'answer_form': answer_form,
    }
    return render(request, 'qna_detail.html', context)

# View untuk menambah pertanyaan (QnA)
@login_required(login_url='/auth/login/')
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user  # Pastikan user ditambahkan ke question
            question.save()
            return JsonResponse({
                'success': True,
                'question': {
                    'title': question.title,
                    'question': question.question,
                    'url': reverse('forum:question_detail', args=[question.id])
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid form data',
                'form_errors': form.errors  # Kirim error form ke frontend
            }, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# View untuk mengedit pertanyaan (QnA)
@login_required(login_url='/auth/login/')
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    # Authorization check
    if request.user != question.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    # Handle POST request for saving the edited question
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Question updated successfully'})
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid data',
                'errors': form.errors  # Send form validation errors to frontend
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

# View untuk menghapus pertanyaan (QnA)
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.user != question.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    question.delete()
    return JsonResponse({'success': True, 'message': 'Question deleted successfully'})

# View untuk menghapus jawaban (Answer)
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)

    if request.user == answer.user or request.user.is_staff:
        answer.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user == comment.user or request.user.is_staff:
        comment.delete()
        return JsonResponse({'success': True, 'message': 'Comment deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
