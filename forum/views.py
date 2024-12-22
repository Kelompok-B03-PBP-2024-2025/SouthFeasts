from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from forum.models import Article, Comment, Question, Answer
from forum.forms import ArticleForm, CommentForm, QuestionForm, AnswerForm
from django.urls import reverse
from django.db.models import Count
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.core.files.base import ContentFile

def show_main(request):
    user = request.user
    filter_type = request.GET.get('filter', 'public_articles')

    # Filter articles based on filter_type
    if filter_type == 'public_articles':
        articles = Article.objects.all().order_by('-created_at')
    elif filter_type == 'your_articles':
        if user.is_authenticated:
            articles = Article.objects.filter(user=user).order_by('-created_at')
        else:
            articles = Article.objects.all().order_by('-created_at')
    else:
        articles = Article.objects.none()
    
    # Filter questions based on filter_type
    if filter_type == 'public_qna':
        questions = Question.objects.annotate(total_answers=Count('answers')).order_by('-created_at')
    elif filter_type == 'your_qna' and user.is_authenticated:
        # Filter hanya pertanyaan yang dibuat oleh pengguna
        questions = Question.objects.filter(user=user).annotate(total_answers=Count('answers')).order_by('-created_at')
    else:
        # Default ke public QnA jika filter tidak dikenali
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
@login_required(login_url='/auth/login/')
def edit_article(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            if 'remove_thumbnail' in request.POST:
                article.thumbnail_file.delete(save=False)
                article.thumbnail_file = None
            form.save()

            # Check if the request is AJAX, if so, return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Article updated successfully',
                    'article': {
                        'id': article.id,
                        'title': article.title,
                        'content': article.content,
                        'thumbnail_img': article.thumbnail_file.url if article.thumbnail_file else '/static/image/default-thumbnail.jpg',
                        'author': article.user.username,
                        'created_at': article.created_at.strftime('%d %b, %Y'),
                    }
                })
            return redirect(reverse('forum:show_main') + '#articles-section')
    
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

    if request.user != question.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    question.delete()
    return JsonResponse({'success': True, 'message': 'Question deleted successfully'})

# View delete answer
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)

    if request.user == answer.user or request.user.is_staff:
        answer.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

# View delete comment
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user == comment.user or request.user.is_staff:
        comment.delete()
        return JsonResponse({'success': True, 'message': 'Comment deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

def show_json_article(request):
    filter_type = request.GET.get('filter', 'public_articles')
    
    if filter_type == 'public_articles':
        queryset = Article.objects.all()
    elif filter_type == 'your_articles' and request.user.is_authenticated:
        queryset = Article.objects.filter(user=request.user)
    else:
        queryset = Article.objects.none()

    # Optimize query
    queryset = queryset.prefetch_related('comments__user').order_by('-created_at')

    articles = []
    for article in queryset:
        comments = []
        for comment in article.comments.all():
            comments.append({
                "id": comment.id,
                "content": comment.content,
                "author": comment.user.username,
                "created_at": comment.created_at.isoformat()  # Gunakan ISO format
            })
            
        article_data = {
            "model": "article",
            "pk": str(article.id),
            "fields": {
                "title": article.title,
                "content": article.content,
                "thumbnail_img": article.get_thumbnail(),
                "author": article.user.username,
                "created_at": article.created_at.isoformat(),  # Gunakan ISO format
                "comments": comments,
                "can_edit": request.user == article.user if request.user.is_authenticated else False,
                "is_staff": request.user.is_staff if request.user.is_authenticated else False
            }
        }
        articles.append(article_data)

    return JsonResponse(articles, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 2
    })

def show_json_qna(request):
    filter_type = request.GET.get('filter', 'public_qna')
    page = int(request.GET.get('page', 1))
    question_id = request.GET.get('question_id')
    per_page = 6

    if question_id:
        try:
            question = Question.objects.get(pk=question_id)
            answers = question.answers.select_related('user').order_by('-created_at')
            
            formatted_answers = [{
                'model': 'answer',
                'pk': str(answer.id),
                'fields': {
                    'content': answer.content,
                    'author': answer.user.username,
                    'created_at': answer.created_at.strftime('%d %b, %Y'),
                    'can_edit': request.user == answer.user if request.user.is_authenticated else False,
                    'is_staff': request.user.is_staff if request.user.is_authenticated else False,
                }
            } for answer in answers]

            return JsonResponse({
                'model': 'question',
                'pk': str(question.id),
                'fields': {
                    'title': question.title,
                    'question': question.question,
                    'author': question.user.username,
                    'created_at': question.created_at.strftime('%d %b, %Y'),
                    'answered': question.answered,
                    'can_edit': request.user == question.user if request.user.is_authenticated else False,
                    'is_staff': request.user.is_staff if request.user.is_authenticated else False,
                    'answers': formatted_answers,
                    'total_answers': len(formatted_answers)
                }
            }, json_dumps_params={'ensure_ascii': False})
        except Question.DoesNotExist:
            return JsonResponse({'error': 'Question not found'}, status=404)

    if filter_type == 'public_qna':
        queryset = Question.objects.all()
    elif filter_type == 'your_qna' and request.user.is_authenticated:
        queryset = Question.objects.filter(user=request.user)
    else:
        queryset = Question.objects.none()

    # Optimize query with prefetch_related
    queryset = queryset.prefetch_related('answers__user').annotate(
        answer_count=Count('answers')
    ).order_by('-created_at')

    paginator = Paginator(queryset, per_page)
    current_page = paginator.get_page(page)

    results = [{
        'model': 'question',
        'pk': str(question.id),
        'fields': {
            'title': question.title,
            'question': question.question,
            'author': question.user.username,
            'created_at': question.created_at.strftime('%d %b, %Y'),
            'answered': question.answered,
            'answer_count': question.answer_count,
            'url': reverse('forum:question_detail', args=[question.id]),
            'can_edit': request.user == question.user if request.user.is_authenticated else False,
            'is_staff': request.user.is_staff if request.user.is_authenticated else False,
            'answers': [{
                'model': 'answer',
                'pk': str(answer.id),
                'fields': {
                    'content': answer.content,
                    'author': answer.user.username,
                    'created_at': answer.created_at.strftime('%d %b, %Y'),
                    'can_edit': request.user == answer.user if request.user.is_authenticated else False,
                    'is_staff': request.user.is_staff if request.user.is_authenticated else False,
                }
            } for answer in question.answers.all()]
        }
    } for question in current_page]

    return JsonResponse({
        'results': results,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'has_previous': current_page.has_previous(),
        'has_next': current_page.has_next(),
        'filter_type': filter_type
    }, json_dumps_params={'ensure_ascii': False})


def delete_article_flutter(request, article_id=None):
    if request.method == 'GET' and article_id:
        try:
            article = Article.objects.get(pk=article_id)
            if article.user != request.user and not request.user.is_staff:
                return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)
            article.delete()
            try:
                Article.objects.get(pk=article_id)
                return JsonResponse({"success": False, "message": "Article deletion failed"}, status=500)
            except Article.DoesNotExist:
                return JsonResponse({"success": True, "message": "Article deleted successfully"})
        except Article.DoesNotExist:
            return JsonResponse({"success": False, "message": "Article not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Invalid request method or action"}, status=405)

@csrf_exempt
def article_flutter(request, article_id=None):
    try:
        # CREATE
        if request.method == 'POST' and not article_id:
            if not request.user.is_authenticated:
                return JsonResponse({"success": False, "message": "User not authenticated"}, status=403)

            # Ambil data dari request.POST
            title = request.POST.get('title')
            content = request.POST.get('content')
            image = request.FILES.get('image')  # Ambil file dari request.FILES

            # Validasi input
            if not title or not content:
                return JsonResponse({"success": False, "message": "Title and content are required"}, status=400)

            # Validasi file gambar (jika ada)
            if image:
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                file_extension = os.path.splitext(image.name)[1].lower()
                if file_extension not in allowed_extensions:
                    return JsonResponse({
                        "success": False,
                        "message": f"Unsupported image format. Allowed formats: {', '.join(allowed_extensions)}."
                    }, status=400)

            # Simpan artikel baru
            article = Article.objects.create(
                title=title,
                content=content,
                user=request.user
            )

            # Simpan gambar jika ada
            if image:
                article.thumbnail_file.save(image.name, image, save=True)

            return JsonResponse({
                "success": True,
                "message": "Article created successfully",
                "article": {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "thumbnail_img": article.get_thumbnail(),
                    "author": article.user.username,
                    "can_edit": True,
                    "created_at": article.created_at.strftime('%d %b, %Y')
                }
            }, status=201)

        # EDIT
        elif request.method == 'POST' and article_id:
            article = Article.objects.get(pk=article_id)

            if request.user != article.user and not request.user.is_staff:
                return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

            # Ambil data dari request.POST
            title = request.POST.get('title')
            content = request.POST.get('content')
            image = request.FILES.get('image')  # Ambil file dari request.FILES

            # Update data artikel
            if title:
                article.title = title
            if content:
                article.content = content
            if image:
                article.thumbnail_file.save(image.name, image, save=True)

            article.save()

            return JsonResponse({
                "success": True,
                "message": "Article updated successfully",
                "article": {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "thumbnail_img": article.get_thumbnail(),
                    "author": article.user.username,
                    "can_edit": True,
                    "created_at": article.created_at.strftime('%d %b, %Y')
                }
            }, status=200)

        return JsonResponse({"success": False, "message": "Invalid request method or action"}, status=405)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@csrf_exempt
def question_flutter(request, question_id=None):
    try:
        # CREATE
        if request.method == 'POST' and not question_id:
            if not request.user.is_authenticated:
                return JsonResponse({"success": False, "message": "User not authenticated"}, status=403)

            data = json.loads(request.body)
            question = Question.objects.create(
                title=data['title'],
                question=data['question'],
                user=request.user
            )

            return JsonResponse({
                "success": True,
                "message": "Question created successfully",
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "question": question.question,
                    "created_at": question.created_at.strftime('%d %b, %Y')
                }
            }, status=201)

        # EDIT
        elif request.method == 'POST' and question_id:
            question = Question.objects.get(pk=question_id)
            
            if request.user != question.user:
                return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

            data = json.loads(request.body)
            question.title = data.get('title', question.title)
            question.question = data.get('question', question.question)
            question.save()

            return JsonResponse({
                "success": True,
                "message": "Question updated successfully",
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "question": question.question,
                    "created_at": question.created_at.strftime('%d %b, %Y')
                }
            })

        # DELETE
        elif request.method == 'DELETE' and question_id:
            try:
                # Ambil question berdasarkan ID
                question = Question.objects.get(pk=question_id)

                # Validasi hak akses
                if request.user != question.user and not request.user.is_staff:
                    return JsonResponse({
                        "success": False,
                        "message": "You don't have permission to delete this question"
                    }, status=403)

                # Hapus question
                question.delete()

                return JsonResponse({
                    "success": True,
                    "message": "Question deleted successfully"
                }, status=200)

            except Question.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": "Question not found"
                }, status=404)

            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "message": str(e)
                }, status=400)
        return JsonResponse({"success": False, "message": "Invalid request method or action"}, status=405)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@csrf_exempt
def comment_flutter(request, comment_id=None):
    try:
        # CREATE
        if request.method == 'POST' and not comment_id:
            if not request.user.is_authenticated:
                return JsonResponse({"success": False, "message": "User not authenticated"}, status=403)

            data = json.loads(request.body)
            article = Article.objects.get(pk=data['article_id'])

            comment = Comment.objects.create(
                article=article,
                user=request.user,
                content=data['content']
            )

            return JsonResponse({
                    "success": True,
                    "message": "Comment created successfully",
                    "comment": {
                    "id": comment.id,
                    "content": comment.content,
                    "author": comment.user.username,
                    "created_at": comment.created_at.strftime('%d %b, %Y'),
                    "can_edit": True,
                    "is_staff": request.user.is_staff
                }
            }, status=201)

        # DELETE
        elif request.method == 'POST' and comment_id:
            action = request.POST.get('action', '').lower()
            if action == 'delete':
                comment = Comment.objects.get(pk=comment_id)
                
                if request.user != comment.user and not request.user.is_staff:
                    return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

                comment.delete()
                return JsonResponse({"success": True, "message": "Comment deleted successfully"})

        return JsonResponse({"success": False, "message": "Invalid request method or action"}, status=405)

    except Comment.DoesNotExist:
        return JsonResponse({"success": False, "message": "Comment not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@csrf_exempt
def answer_flutter(request, answer_id=None):
    try:
        # CREATE
        if request.method == 'POST' and not answer_id:
            if not request.user.is_authenticated:
                return JsonResponse({"success": False, "message": "User not authenticated"}, status=403)

            data = json.loads(request.body)
            question = Question.objects.get(pk=data['question_id'])

            answer = Answer.objects.create(
                question=question,
                user=request.user,
                content=data['content']
            )

            # Update question answered status
            question.answered = True
            question.save()

            return JsonResponse({
                "success": True,
                "message": "Answer created successfully",
                "answer": {
                    "id": answer.id,
                    "content": answer.content,
                    "author": answer.user.username,
                    "created_at": answer.created_at.strftime('%d %b, %Y'),
                    "can_edit": True,
                    "is_staff": request.user.is_staff  # Tambahkan ini
                }
            }, status=201)

        # DELETE
        elif request.method == 'POST' and answer_id:
            action = request.POST.get('action', '').lower()
            if action == 'delete':
                answer = Answer.objects.get(pk=answer_id)
                
                if request.user != answer.user and not request.user.is_staff:
                    return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

                question = answer.question
                answer.delete()

                # Update question answered status if no answers remain
                if question.answers.count() == 0:
                    question.answered = False
                    question.save()

                return JsonResponse({"success": True, "message": "Answer deleted successfully"})

        return JsonResponse({"success": False, "message": "Invalid request method or action"}, status=405)

    except Answer.DoesNotExist:
        return JsonResponse({"success": False, "message": "Answer not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)

@csrf_exempt
def delete_question_flutter(request, question_id=None):
    if request.method == 'GET' and question_id:
        try:
            question = Question.objects.get(pk=question_id)
            if question.user != request.user and not request.user.is_staff:
                return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)
            question.delete()
            try:
                Question.objects.get(pk=question_id)
                return JsonResponse({"success": False, "message": "Question deletion failed"}, status=500)
            except Question.DoesNotExist:
                return JsonResponse({"success": True, "message": "Question deleted successfully"})
        except Question.DoesNotExist:
            return JsonResponse({"success": False, "message": "Question not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Invalid request method or action"}, status=405)