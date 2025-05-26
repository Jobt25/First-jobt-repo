from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class AuthAPITestCase(APITestCase):
    def test_register_user(self):
        url = reverse('register')  # Make sure 'register' is in your urls.py
        data = {
            "email": "test@example.com",
            "phone_number": "+2348161589374",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('email' in response.data)

    def test_login_user(self):
        # First register a user
        self.test_register_user()
        
        # Now test login
        url = reverse('login')  # Make sure 'login' is in your urls.py
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)

    def test_register_invalid_data(self):
        url = reverse('register')
        invalid_data = {
            "email": "lawalht@gmail.com",
            "phone_number": "123",
            "password": "short",
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_credentials(self):
        url = reverse('login')
        invalid_data = {
            "email": "lawal",
            "password": "shhhhhort"
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)