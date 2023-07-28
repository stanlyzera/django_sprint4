from django.urls import path, include

from . import views

app_name = 'blog'


post_urls = [
    path('<int:post_pk>/',
         views.PostDetailView.as_view(), name='post_detail'),
    path('create/',
         views.PostCreateView.as_view(), name='create_post'),
    path('<int:post_pk>/edit/',
         views.PostUpdateView.as_view(), name='edit_post'),
    path('<int:post_pk>/delete/',
         views.PostDeleteView.as_view(), name='delete_post'),
    path('<int:post_pk>/comment',
         views.CommentCreateView.as_view(), name='add_comment'),
    path('<int:post_pk>/edit_comment/<int:comment_pk>',
         views.CommentUpdateView.as_view(), name='edit_comment'),
    path('<int:post_pk>/delete_comment/<int:comment_pk>/',
         views.CommentDeleteView.as_view(), name='delete_comment'),
]
urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('posts/', include(post_urls)),
    path('profile/<str:username>/',
         views.ProfileListView.as_view(),
         name='profile'),
    path('account/edit/',
         views.ProfileUpdateView.as_view(),
         name='edit_profile'),
    path('category/<slug:category_slug>/',
         views.CategoryPostListView.as_view(),
         name='category_posts'),

]
