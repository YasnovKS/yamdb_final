import uuid

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from reviews.models import Category, Comment, Genre, GenreTitle, Review, Title
from reviews.validators import validate_not_future_year
from users.models import User


class CategorySerializer(serializers.ModelSerializer):

    slug = serializers.SlugField(
        max_length=50,
        validators=[
            UniqueValidator(
                queryset=Category.objects.all(),
                message='Указанная категория уже есть в БД',
            )
        ],
    )

    class Meta:
        model = Category
        fields = (
            'name',
            'slug',
        )


class GenreSerializer(serializers.ModelSerializer):

    slug = serializers.SlugField(
        max_length=50,
        validators=[
            UniqueValidator(
                queryset=Genre.objects.all(),
                message='Указанный жанр уже есть в БД',
            )
        ],
    )

    class Meta:
        model = Genre
        fields = (
            'name',
            'slug',
        )


class ReadOnlyTitleSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField()
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'description',
            'rating',
            'genre',
            'category',
        )


class TitleSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        many=True, slug_field='slug', queryset=Genre.objects.all()
    )
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all()
    )

    year = serializers.IntegerField(validators=[validate_not_future_year])

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'description',
            'genre',
            'category',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Title.objects.all(),
                fields=('name', 'year', 'category'),
                message='Такое произведение уже существует в БД',
            )
        ]

    def create(self, validated_data):
        genres = validated_data.pop('genre')
        title = Title.objects.create(**validated_data)
        for genre in genres:
            GenreTitle.objects.create(genre=genre, title=title)
        return title

    def update(self, instance, validated_data):
        genres = (
            validated_data.pop('genre') if 'genre' in validated_data else []
        )

        # setting new values to model instance
        for fieldname, value in validated_data.items():
            setattr(instance, fieldname, value)

        # delete all current genres-title entries and add new ones
        GenreTitle.objects.filter(title=instance).delete()
        for genre in genres:
            current_genre = Genre.objects.get(**genre)
            GenreTitle.objects.create(genre=current_genre, title=instance)

        # saving updates to db and return updated instance
        instance.save()
        return instance


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150,
                                     required=True
                                     )
    email = serializers.EmailField(max_length=254,
                                   required=True
                                   )

    class Meta:
        fields = ('username', 'email')

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        queryset = User.objects.filter(Q(username=username)
                                       | Q(email=email)).values()
        if not queryset:
            confirmation_code = str(uuid.uuid4())
            data['confirmation_code'] = confirmation_code
            return data
        for object in queryset:
            if object['username'] == username and object['email'] == email:
                return data
            if object['username'] == username:
                raise serializers.ValidationError('Пользователь с таким '
                                                  'именем уже существует.')
            if object['email'] == email:
                raise serializers.ValidationError('Пользователь с указанным '
                                                  'e-mail адресом уже '
                                                  'существует.')

    def validate_username(self, value):
        '''
        Checking rules for creating a username.
        '''
        MIN_LENGTH = 2  # Minimum number of characters in username.

        if value == "me":
            raise serializers.ValidationError('Вы не можете использовать "me"'
                                              ' в качестве имени пользователя.'
                                              )
        if len(value) < MIN_LENGTH:
            raise serializers.ValidationError('Имя пользователя не может быть'
                                              ' короче 2-х знаков.'
                                              )
        return value

    def validate_email(self, value):
        '''
        Checking rules for creating an e-mail.
        '''
        MIN_LENGTH = 5  # Minimum number of characters in e-mail.

        if len(value) < MIN_LENGTH:
            raise serializers.ValidationError('Некорректно введен адрес '
                                              'электронной почты.'
                                              )
        return value


class ObtainTokenSerializer(serializers.Serializer):
    '''
    Serializer for getting token after registration.
    '''
    username = serializers.CharField(max_length=150,
                                     required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')

    def validate(self, data):
        '''
        Checking that user entered right confirmation_code.
        '''
        user = get_object_or_404(User, username=data.get('username'))
        if data.get('confirmation_code') != user.confirmation_code:
            raise serializers.ValidationError(
                'Введен неверный' ' проверочный код.'
            )
        return data


class UsersManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )


class SelfProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )
        read_only_fields = ('role',)


class CreateTitleDefault(object):
    requires_context = True

    def __call__(self, serializer_field):
        view = serializer_field.context['view']
        title_id = view.kwargs.get('title_id')
        return get_object_or_404(Title, pk=title_id)


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )
    score = serializers.IntegerField(min_value=1, max_value=10)
    title = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(CreateTitleDefault())
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date', 'title')
        validators = [
            UniqueTogetherValidator(
                queryset=Review.objects.all(), fields=['author', 'title']
            )
        ]


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
