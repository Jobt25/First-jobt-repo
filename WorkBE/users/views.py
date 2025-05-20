from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import UserRegisterSerializer, UserLoginSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        request_body=UserRegisterSerializer,
        responses={
            status.HTTP_201_CREATED: UserRegisterSerializer,
            status.HTTP_400_BAD_REQUEST: "Invalid input data"
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    @swagger_auto_schema(
        operation_description="Authenticate user and get JWT tokens",
        request_body=UserLoginSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Authentication successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            status.HTTP_400_BAD_REQUEST: "Invalid input data",
            status.HTTP_401_UNAUTHORIZED: "Invalid credentials"
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Check if any error has the 'authorization' code
            errors = serializer.errors.get('non_field_errors', [])
            for error in errors:
                # Check if the error has the code 'authorization'
                if hasattr(error, 'code') and error.code == 'authorization':
                    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
            # Return 400 for other validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(serializer.validated_data, status=status.HTTP_200_OK)