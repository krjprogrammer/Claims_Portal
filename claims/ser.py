from rest_framework import serializers
from .models import PortalUser, PortalRoles, PortalPages


class PortalPagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalPages
        fields = ['id', 'name']

from django.db.models import Exists, OuterRef

from rest_framework import serializers

class PortalRolesSerializer(serializers.ModelSerializer):
    is_occupied = serializers.SerializerMethodField()

    access_pages = PortalPagesSerializer(many=True, read_only=True)

    access_pages_ids = serializers.PrimaryKeyRelatedField(
        queryset=PortalPages.objects.all(),
        many=True,
        write_only=True,
        source='access_pages',
        required=False
    )

    class Meta:
        model = PortalRoles
        fields = [
            'id',
            'name',
            'is_occupied',
            'access_pages',
            'access_pages_ids'
        ]

    def get_is_occupied(self, obj):
        return getattr(
            obj,
            'is_occupied',
            PortalUser.objects.filter(role=obj).exists()
        )

    def create(self, validated_data):
        pages = validated_data.pop('access_pages', [])
        role = PortalRoles.objects.create(**validated_data)
        role.access_pages.set(pages)
        return role

    def update(self, instance, validated_data):
        pages = validated_data.pop('access_pages', None)

        instance = super().update(instance, validated_data)

        if pages is not None:
            instance.access_pages.set(pages)

        return instance

class PortalUserSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=PortalRoles.objects.all(), required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = PortalUser
        fields = ['id', 'username', 'email', 'role', 'status', 'first_name', 'last_name', 'password', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class PortalUserShowSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.name', read_only=True, allow_null=True)
    is_superadmin = serializers.ReadOnlyField()
    accessible_pages = serializers.SerializerMethodField()

    class Meta:
        model = PortalUser
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name', 'status', 'last_login', 'is_superadmin', 'accessible_pages', 'totp_enabled']

    def get_accessible_pages(self, user):
        if user.is_superadmin:
            return PortalPagesSerializer(PortalPages.objects.all(), many=True).data
        if user.role:
            return PortalPagesSerializer(user.role.access_pages.all(), many=True).data
        return []


class RegisterSaveSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True, min_length=4)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=4)
    role = serializers.PrimaryKeyRelatedField(
        queryset=PortalRoles.objects.all(),
        required=True
    )

    class Meta:
        model = PortalUser
        fields = [
            'id', 'username', 'email', 'password',
            'confirm_password', 'role', 'status',
            'first_name', 'last_name'
        ]

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match.")

        # Generate username from email if not provided
        username = data.get('username')
        if not username:
            username = data['email'].split('@')[0]
            data['username'] = username

        if PortalUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists.")

        if PortalUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists.")

        return data

    def create(self, validated_data):
        password = validated_data.pop('password')

        user = PortalUser(**validated_data)
        user.temp_password = password  # read by post_save signal before it's lost
        user.set_password(password)
        user.is_active = True
        user.save()

        return user


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
