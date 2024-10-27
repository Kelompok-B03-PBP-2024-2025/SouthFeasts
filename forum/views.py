from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from forum.models import Article, Comment, Question, Answer
from forum.forms import ArticleForm, CommentForm, QuestionForm, AnswerForm
from django.urls import reverse
from django.db.models import Count

def show_main(request):
    user = request.user
    filter_type = request.GET.get('filter', 'public_articles')

    # Filter articles based on filter_type
    if filter_type == 'public_articles':
        articles = Article.objects.exclude(user=user).order_by('-created_at') 
    elif filter_type == 'your_articles':
        articles = Article.objects.filter(user=user).order_by('-created_at')  
    else:
        articles = Article.objects.all().order_by('-created_at')         

    # Filter questions based on filter_type
    if filter_type == 'public_qna':
        questions = Question.objects.exclude(user=user).annotate(total_answers=Count('answers')).order_by('-created_at')  
    elif filter_type == 'your_qna':
        questions = Question.objects.filter(user=user).annotate(total_answers=Count('answers')).order_by('-created_at')   
    else:
        questions = Question.objects.annotate(total_answers=Count('answers')).order_by('-created_at')               

    # Initialize forms for new article and question
    article_form = ArticleForm()
    question_form = QuestionForm()

    context = {
        'articles': articles,
        'questions': questions,
        'article_form': article_form,
        'question_form': question_form,
        'current_filter': filter_type,
    }
    return render(request, 'culinary_insights.html', context)

# View article detail (content) and comments
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

# View add new article
@login_required(login_url='/auth/login/')
def add_article(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        
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
                    'thumbnail_img': article.get_thumbnail() or '/static/image/default-thumbnail.jpg',
                    'author': article.user.username,
                    'created_at': article.created_at.strftime('%d %b, %Y'),
                    'url': reverse('forum:article_detail', args=[article.id]),
                }
            })

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# View edit article
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            if form.cleaned_data.get('remove_thumbnail'):
                article.thumbnail_file.delete(save=False)
                article.thumbnail_file = None
            form.save()
            return redirect('forum:article_detail', article_id=article.id)

    else:
        form = ArticleForm(instance=article)
    
    return render(request, 'edit_article.html', {'form': form, 'article': article})

# View delete article
def delete_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.user != article.user and not request.user.is_staff:
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

    article.delete()
    return redirect(reverse('forum:show_main') + '#articles-section')

# View QnA detail and answers
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

# View add new question
@login_required(login_url='/auth/login/')
def add_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user  
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
                'form_errors': form.errors  
            }, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

# View edit question
@login_required(login_url='/auth/login/')
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    # Authorization check
    if request.user != question.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Question updated successfully'})
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid data',
                'errors': form.errors 
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

# View delete QnA
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.user != question.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    question.delete()
    return JsonResponse({'success': True, 'message': 'Question deleted successfully'})

# View delete answer
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)

    if request.user == answer.user:
        answer.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

# View delete comment
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user == comment.user:
        comment.delete()
        return JsonResponse({'success': True, 'message': 'Comment deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
