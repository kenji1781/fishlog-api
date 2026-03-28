from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginTokenSerializer, SignupSerializer

class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = LoginTokenSerializer.get_token(user)
        return Response(
            {
                "id": user.id,
                "account_name": user.account_name,
                "email": user.email,
                "refresh": str(token),
                "access": str(token.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginTokenSerializer
    permission_classes = [AllowAny]
