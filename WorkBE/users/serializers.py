from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import User
from drf_yasg import openapi

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number',
            'first_name', 'last_name', 'date_of_birth',
            'is_active', 'created_at'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'is_active': {'read_only': True},
            'created_at': {'read_only': True},
        }

    @classmethod
    def get_swagger_schema(cls):
        return {
            'type': openapi.TYPE_OBJECT,
            'title': 'User',
            'properties': {
                'id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Unique identifier for the user'
                ),
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email address',
                    format='email'
                ),
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User phone number'
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User first name'
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User last name'
                ),
                'date_of_birth': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User date of birth (YYYY-MM-DD)',
                    format='date'
                ),
                'is_active': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Indicates if the user account is active'
                ),
                'created_at': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Timestamp when the user was created',
                    format='date-time'
                ),
            },
            'required': ['email', 'phone_number', 'first_name', 'last_name']
        }

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'email', 'phone_number', 'password',
            'first_name', 'last_name', 'date_of_birth',
            'id_type', 'id_number'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'id_type': {'required': False},
            'id_number': {'required': False},
        }

    @classmethod
    def get_swagger_schema(cls):
        return {
            'type': openapi.TYPE_OBJECT,
            'title': 'UserRegister',
            'properties': {
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email address',
                    format='email'
                ),
                'phone_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User phone number'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User password (write-only)',
                    format='password'
                ),
                'first_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User first name'
                ),
                'last_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User last name'
                ),
                'date_of_birth': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User date of birth (YYYY-MM-DD, optional)',
                    format='date'
                ),
                'id_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Type of identification (optional)'
                ),
                'id_number': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Identification number (optional)'
                ),
            },
            'required': ['email', 'phone_number', 'password', 'first_name', 'last_name']
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            date_of_birth=validated_data.get('date_of_birth'),
            id_type=validated_data.get('id_type'),
            id_number=validated_data.get('id_number'),
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    @classmethod
    def get_swagger_schema(cls):
        return {
            'type': openapi.TYPE_OBJECT,
            'title': 'UserLogin',
            'properties': {
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User email address',
                    format='email'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='User password (write-only)',
                    format='password'
                ),
                'access': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='JWT access token (read-only)'
                ),
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='JWT refresh token (read-only)'
                ),
            },
            'required': ['email', 'password']
        }

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Both email and password are required", code='authorization')
        
        try:
            user = authenticate(email=email, password=password)
            
            if not user:
                raise serializers.ValidationError("Invalid credentials", code='authorization')
            
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled", code='authorization')
            
            refresh = RefreshToken.for_user(user)
            user.last_login = timezone.now()
            user.save()
            
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'email': user.email,
            }
            
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Invalid credentials", code='authorization')