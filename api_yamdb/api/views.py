import uuid

from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (filters, mixins, permissions, status, views,
                            viewsets)
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from api_yamdb.settings import SERVICE_EMAIL
from .filters import TitleFilter
from .mixins import ListCreateDestroyViewSet
from .permissions import AuthorPermission, IsAdminOrReadOnly, IsAdminPermission
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ObtainTokenSerializer,
                          ReadOnlyTitleSerializer, RegisterSerializer,
                          ReviewSerializer, SelfProfileSerializer,
                          TitleSerializer, UsersManageSerializer)
from reviews.models import Category, Genre, Review, Title
from users.models import User


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    '''
    This viewset is intended for registration new users. Also users can
    get their confirmation code if registration was by person who had
    role "admin".
    '''

    serializer_class = RegisterSerializer

    def send_email(self, user):
        confirmation_code = user.confirmation_code
        email = user.email
        send_mail(
            'E-mail verification',
            f'Your confirmation_code is {confirmation_code}',
            SERVICE_EMAIL,
            [email]
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, created = User.objects.get_or_create(**serializer.validated_data)
        self.send_email(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ObtainTokenView(views.APIView):
    '''
    This is a viewset for obtaining token by entering user "username"
    and "confirmation code".
    '''

    def post(self, request):
        serializer = ObtainTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.data.get('username')
        user = get_object_or_404(User, username=username)
        token = RefreshToken.for_user(user).access_token
        return Response({'token': str(token)}, status=status.HTTP_200_OK)


class UsersManageViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersManageSerializer
    lookup_field = 'username'
    pagination_class = PageNumberPagination
    permission_classes = (IsAuthenticated, IsAdminPermission)

    def perform_create(self, serializer):
        confirmation_code = str(uuid.uuid4())
        serializer.save(confirmation_code=confirmation_code)

    @action(
        methods=['get', 'patch'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        profile = User.objects.get(pk=request.user.id)
        if request.method == "GET":
            serializer = SelfProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = SelfProfileSerializer(
            request.user, data=self.request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class SlugNameViewSet(ListCreateDestroyViewSet):
    lookup_field = 'slug'
    permission_classes = (
        IsAdminOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly,
    )
    filter_backends = (filters.SearchFilter,)
    search_fields = ('$name',)
    pagination_class = PageNumberPagination


class CategoryViewSet(SlugNameViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(SlugNameViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg('reviews__score'))
    permission_classes = (
        IsAdminOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filter_class = TitleFilter
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return TitleSerializer
        return ReadOnlyTitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (AuthorPermission, IsAuthenticatedOrReadOnly)
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        serializer.save(title=title, author=self.request.user)

    def get_queryset(self):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        return title.reviews.all()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (AuthorPermission, IsAuthenticatedOrReadOnly)
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            pk=self.kwargs.get('review_id'),
            title=self.kwargs.get('title_id')
        )
        serializer.save(review=review, author=self.request.user)

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            pk=self.kwargs.get('review_id'),
            title=self.kwargs.get('title_id')
        )
        return review.comments.all()
