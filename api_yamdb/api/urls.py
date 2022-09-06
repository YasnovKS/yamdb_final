from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (CategoryViewSet, CommentViewSet, GenreViewSet,
                    ObtainTokenView, RegisterViewSet, ReviewViewSet,
                    TitleViewSet, UsersManageViewSet)

app_name = 'api'

router_v1 = SimpleRouter()

router_v1.register('auth/signup', RegisterViewSet, basename='register')
router_v1.register('users', UsersManageViewSet, basename='users')
router_v1.register('categories', CategoryViewSet, basename='category')
router_v1.register('genres', GenreViewSet, basename='genre')
router_v1.register('titles', TitleViewSet, basename='title')
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews',
)
router_v1.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments',
)

urlpatterns = [
    path('v1/', include(router_v1.urls), name='api'),
    path('v1/auth/token/', ObtainTokenView.as_view(), name='token'),
]
