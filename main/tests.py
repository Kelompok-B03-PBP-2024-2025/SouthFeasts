from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class ShowMainViewTests(TestCase):

    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_show_main_view_with_authenticated_user(self):
        # Log in the user
        self.client.login(username='testuser', password='password123')

        # Get the response from the show_main view
        response = self.client.get(reverse('main:show_main'))

        # Check that the response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that the correct template is used
        self.assertTemplateUsed(response, 'main.html')

        # Check that the context contains the user
        self.assertEqual(response.context['user'], self.user)

    def test_show_main_view_with_anonymous_user(self):
        # Get the response from the show_main view without logging in
        response = self.client.get(reverse('main:show_main'))

        # Check that the response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that the correct template is used
        self.assertTemplateUsed(response, 'main.html')

        # Check that the context user is AnonymousUser
        self.assertEqual(str(response.context['user']), 'AnonymousUser')
