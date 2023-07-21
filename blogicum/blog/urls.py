from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('posts/<int:pk>/',
         views.PostDetailView.as_view(),
         name='post_detail'),
    path('category/<slug:category_slug>/',
         views.CategoryPostListView.as_view(),
         name='category_posts'),
    path('post/create/',
         views.PostCreateView.as_view(),
         name='create_post'),
    path('posts/<int:pk>/edit/',
         views.PostUpdateView.as_view(),
         name='edit_post'),
    path('posts/<int:pk>/comment/',
         views.CommentCreateView.as_view(),
         name='add_comment'),
    path('posts/<int:pk>/delete/',
         views.PostDeleteView.as_view(),
         name='delete_post'),
    path('posts/<int:pk>/edit_comment/<int:comment_pk>/',
         views.CommentUpdateView.as_view(),
         name='edit_comment'),
    path('posts/<int:pk>/delete_comment/<int:comment_pk>/',
         views.CommentDeleteView.as_view(),
         name='delete_comment'),
    path('profile/<slug:username>/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/<slug:username>/edit/', views.ProfileUpdateView.as_view(), name='edit_profile'),

]