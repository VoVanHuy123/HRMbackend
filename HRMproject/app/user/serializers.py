from rest_framework import serializers
from .models import User
from employee.serializers import EmployeeSerializer

class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']


class UserSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer()
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['avatar'] = instance.avatar.url if instance.avatar else ''

        return data

    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        u.set_password(u.password)
        u.save()
        return u

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'avatar', 'role',"is_first_access","employee"]
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'role': {'required': True},
        }
        read_only_fields = ('is_staff',)
class CreateUserSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['avatar'] = instance.avatar.url if instance.avatar else ''

        return data

    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        u.set_password(u.password)
        u.save()
        return u

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'avatar', 'role',"is_first_access","employee"]
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'role': {'required': True},
        }
        read_only_fields = ('is_staff',)
class RefreshTokenSerializer(serializers.Serializer):
    # refresh_token = serializers.CharField()
    pass