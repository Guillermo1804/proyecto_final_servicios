from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /auth/login
    
    Body:
    {
        "email": "admin@agm.buap.mx",
        "password": "admin123"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "user": {
                "id": 1,
                "email": "admin@agm.buap.mx",
                "nombre": "Administrador",
                "rol": "admin",
                "activo": true
            }
        },
        "message": "Login exitoso"
    }
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data.get('user')
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'data': {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data
            },
            'message': 'Login exitoso'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'data': None,
        'message': serializer.errors.get('non_field_errors', ['Error en la autenticación'])[0]
    }, status=status.HTTP_401_UNAUTHORIZED)
