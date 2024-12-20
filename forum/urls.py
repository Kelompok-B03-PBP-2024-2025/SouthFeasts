from django.urls import path
from forum.views import *

app_name = 'forum'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('article/<int:article_id>/', article_detail, name='article_detail'),
    path('article/add/', add_article, name='add_article'),
    path('article/edit/<int:article_id>/', edit_article, name='edit_article'),
    path('article/delete/<int:article_id>/', delete_article, name='delete_article'),
    path('question/add/', add_question, name='add_question'),
    path('question/edit/<int:question_id>/', edit_question, name='edit_question'),
    path('question/delete/<int:question_id>/', delete_question, name='delete_question'),
    path('question/<int:question_id>/', question_detail, name='question_detail'),
    path('answer/<int:answer_id>/delete/', delete_answer, name='delete_answer'),
    path('comment/delete/<int:comment_id>/', delete_comment, name='delete_comment'),
    # API for Flutter
    path('json/article/', show_json_article, name='show_json_article'),
    path('json/qna/', show_json_qna, name='show_json_qna'),
    path('api/article/create/', article_flutter, name='create_article_flutter'),
    path('api/article/edit/<int:article_id>/', article_flutter, name='edit_article_flutter'), 
    path('api/article/delete/<int:article_id>/', article_flutter, name='delete_article_flutter'),
    path('api/question/create/', question_flutter, name='create_question_flutter'),
    path('api/question/edit/<int:question_id>/', question_flutter, name='edit_question_flutter'),
    path('api/question/delete/<int:question_id>/', question_flutter, name='delete_question_flutter'),
    path('api/comment/create/', comment_flutter, name='create_comment_flutter'),
    path('api/comment/delete/<int:comment_id>/', comment_flutter, name='delete_comment_flutter'),
    path('api/answer/create/', answer_flutter, name='create_answer_flutter'),
    path('api/answer/delete/<int:answer_id>/', answer_flutter, name='delete_answer_flutter'),
]