from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "account_name",
            "full_name",
            "email",
            "gender",
            "job",
            "age",
            "address",
            "phone_number",
            "other_info",
            "password",
        )

    def validate(self, attrs):
        account_name = attrs.get("account_name")
        email = attrs.get("email")
        if not account_name:
            raise serializers.ValidationError({"account_name": "アカウント名は必須です。"})
        if not email:
            raise serializers.ValidationError({"email": "メールは必須です。"})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["account_name"] = user.account_name
        token["email"] = user.email
        return token
