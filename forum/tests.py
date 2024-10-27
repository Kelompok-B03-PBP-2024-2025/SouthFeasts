from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from forum.models import Article, Question, Comment, Answer

class ForumViewsTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client()
        
        # Log in the user for authenticated actions
        self.client.login(username='testuser', password='testpass')
        
        # Create sample article and question for testing
        self.article = Article.objects.create(user=self.user, title="Test Article", content="Content of the test article.")
        self.question = Question.objects.create(user=self.user, title="Test Question", question="Content of the test question.")

    def test_show_main(self):
        response = self.client.get(reverse('forum:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'culinary_insights.html')

    def test_show_main_filter_public_articles(self):
        response = self.client.get(reverse('forum:show_main') + '?filter=public_articles')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.article, response.context['articles'])

    def test_show_main_filter_your_articles(self):
        response = self.client.get(reverse('forum:show_main') + '?filter=your_articles')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.article, response.context['articles'])

    def test_add_article(self):
        response = self.client.post(reverse('forum:add_article'), {
            'title': 'New Article',
            'content': 'Content for the new article.',
            'thumbnail_file': ''  # Assuming empty file will use default thumbnail
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Article.objects.filter(title="New Article").exists())

    def test_edit_article(self):
        response = self.client.post(reverse('forum:edit_article', args=[self.article.id]), {
            'title': 'Updated Article Title',
            'content': 'Updated content for the article.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Updated Article Title")

    def test_delete_article_authorized(self):
        response = self.client.post(reverse('forum:delete_article', args=[self.article.id]))
        self.assertRedirects(response, reverse('forum:show_main'))
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())

    def test_delete_article_authorized(self):
        response = self.client.post(reverse('forum:delete_article', args=[self.article.id]))
        self.assertRedirects(response, reverse('forum:show_main') + '#articles-section')
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())

    def test_add_question(self):
        response = self.client.post(reverse('forum:add_question'), {
            'title': 'New Question',
            'question': 'What is the content of the new question?',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Question.objects.filter(title="New Question").exists())

    def test_edit_question(self):
        response = self.client.post(reverse('forum:edit_question', args=[self.question.id]), {
            'title': 'Updated Question Title',
            'question': 'Updated content for the question.',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.question.refresh_from_db()
        self.assertEqual(self.question.title, "Updated Question Title")

    def test_delete_question_authorized(self):
        response = self.client.post(reverse('forum:delete_question', args=[self.question.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())

    def test_delete_question_unauthorized(self):
        new_user = User.objects.create_user(username='newuser', password='newpass')
        self.client.login(username='newuser', password='newpass')
        response = self.client.post(reverse('forum:delete_question', args=[self.question.id]))
        self.assertEqual(response.status_code, 403)

    def test_delete_comment_unauthorized(self):
        comment = Comment.objects.create(article=self.article, user=self.user, content="Test comment")
        new_user = User.objects.create_user(username='newuser', password='newpass')
        self.client.login(username='newuser', password='newpass')
        response = self.client.post(reverse('forum:delete_comment', args=[comment.id]))
        self.assertEqual(response.status_code, 403)

    def test_delete_answer_unauthorized(self):
        answer = Answer.objects.create(question=self.question, user=self.user, content="Test answer")
        new_user = User.objects.create_user(username='newuser', password='newpass')
        self.client.login(username='newuser', password='newpass')
        response = self.client.post(reverse('forum:delete_answer', args=[answer.id]))
        self.assertEqual(response.status_code, 403)

    def test_add_article_unauthenticated(self):
        self.client.logout()
        response = self.client.post(reverse('forum:add_article'), {
            'title': 'Unauthenticated Article',
            'content': 'This should not be added without login.',
        })
        self.assertNotEqual(response.status_code, 200)

    def test_add_question_unauthenticated(self):
        self.client.logout()
        response = self.client.post(reverse('forum:add_question'), {
            'title': 'Unauthenticated Question',
            'question': 'This should not be added without login.',
        })
        self.assertNotEqual(response.status_code, 200)
