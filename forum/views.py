from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from forum.models import Article, Comment, Question, Answer
from forum.forms import ArticleForm, CommentForm, QuestionForm, AnswerForm

# View untuk menampilkan halaman utama (Culinary Insights)
def show_main(request):
    articles = Article.objects.all().order_by('-created_at')
    questions = Question.objects.all().order_by('-created_at')

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
def article_detail(request, article_id):
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return HttpResponseNotFound("Article not found.")

    comments = Comment.objects.filter(article=article)

    # Jika user belum login dan mencoba menambahkan komentar, arahkan ke login
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('auth:login')  # Redirect ke halaman login jika belum login

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
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.user = request.user
            article.save()
            return redirect('forum:show_main')
    return redirect('forum:show_main')

# View untuk menampilkan detail pertanyaan (QnA) dan jawaban
def question_detail(request, question_id):
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return HttpResponseNotFound("Question not found.")

    answers = Answer.objects.filter(question=question)

    # Jika user belum login dan mencoba menambahkan jawaban, arahkan ke login
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('auth:login')  # Redirect ke halaman login jika belum login

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
            question.user = request.user
            question.save()
            return redirect('forum:show_main')
    return redirect('forum:show_main')

# View untuk mengedit artikel
@login_required(login_url='/auth/login/')
def edit_article(request, article_id):
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return HttpResponseNotFound("Article not found.")

    if request.user != article.user:
        return JsonResponse({"success": False}, status=403)

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return JsonResponse({
                "success": True,
                "title": article.title,
                "content": article.content,
            })
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False}, status=405)

# View untuk mengedit pertanyaan (QnA)
@login_required(login_url='/auth/login/')
def edit_question(request, question_id):
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Question not found'}, status=404)

    if request.user != question.user:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'title': question.title, 'question': question.question})
        else:
            return JsonResponse({'success': False, 'message': 'Form is invalid'}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

# View untuk menghapus artikel
@login_required(login_url='/auth/login/')
def delete_article(request, article_id):
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return HttpResponseNotFound("Article not found.")

    if request.user != article.user:
        return HttpResponseForbidden("You are not authorized to delete this article.")

    article.delete()
    return redirect('forum:show_main')

# View untuk menghapus pertanyaan (QnA)
@login_required(login_url='/auth/login/')
def delete_question(request, question_id):
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return HttpResponseNotFound("Question not found.")

    if request.user != question.user:
        return HttpResponseForbidden("You are not authorized to delete this question.")

    question.delete()
    return redirect('forum:show_main')
