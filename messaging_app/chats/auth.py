# messaging_app/chats/auth.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token serializer that includes additional user information
    in the token response and uses email for authentication.
    """
    username_field = "email"  # This will use email field
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the username field to use email
        self.fields[self.username_field] = serializers.EmailField()
        self.fields.pop('username', None)  # remove username field if present
    
    @classmethod
    def get_token(cls, user):
        """
        Override to add custom claims to the token.
        """
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = str(user.user_id)
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        
        return token
    
    def validate(self, attrs):
        """
        Override to authenticate using email instead of username.
        """
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Must include "email" and "password".')
        
        user = authenticate(
            request=self.context.get('request'),
            username=email,  # still called username internally
            password=password
        )

        if not user:
            raise serializers.ValidationError('No active account found with the given credentials')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')

        # Generate tokens the same way as parent
        data = super().validate({'email': email, 'password': password})

        # Attach serialized user data
        data['user'] = UserSerializer(user).data
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom Token view that returns additional user information along with tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(
                {'error': 'Invalid credentials', 'details': e.detail},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user and return JWT tokens.
    """
    serializer = UserSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate tokens for the new user
        token_serializer = CustomTokenObtainPairSerializer()
        tokens = token_serializer.get_token(user)
        
        return Response({
            'access': str(tokens.access_token),
            'refresh': str(tokens),
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_user(request):
    """
    Logout user by blacklisting the refresh token.
    """
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'Invalid token or logout failed',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_profile(request):
    """
    Get current user profile information.
    """
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'User not authenticated'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['PUT', 'PATCH'])
def update_profile(request):
    """
    Update current user profile.
    """
    if not request.user.is_authenticated:
        return Response({
            'error': 'User not authenticated'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    partial = request.method == 'PATCH'
    serializer = UserSerializer(
        request.user, 
        data=request.data, 
        partial=partial,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def change_password(request):
    """
    Change user password.
    """
    if not request.user.is_authenticated:
        return Response({
            'error': 'User not authenticated'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not all([old_password, new_password, confirm_password]):
        return Response({
            'error': 'All password fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({
            'error': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not request.user.check_password(old_password):
        return Response({
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate new password
    from django.contrib.auth.password_validation import validate_password
    try:
        validate_password(new_password, request.user)
    except Exception as e:
        return Response({
            'error': 'Password validation failed',
            'details': list(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.set_password(new_password)
    request.user.save()
    
    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)