from django.http import Http404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q

from .forms import PostForm, CommentForm
from .models import Post, Category, Comment
from django.contrib.auth.models import User
from django.conf import settings


class PostFormMixin:
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm


class CommentUpdateMixin:
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def get_object(self, queryset=None):
        post_pk = self.kwargs.get('post_pk')
        comment_pk = self.kwargs.get('comment_pk')
        comment = get_object_or_404(Comment, pk=comment_pk, post__pk=post_pk)
        if comment.author != self.request.user:
            raise Http404(
                "У вас нет прав для редактирования этого комментария"
            )
        return comment

    def get_success_url(self):
        post = self.object.post
        return reverse('blog:post_detail', kwargs={'post_pk': post.pk})


class PostUpdateMixin:
    def get_object(self, queryset=None):
        post_pk = self.kwargs.get('post_pk')
        if queryset is None:
            queryset = self.get_queryset()
        try:
            return queryset.get(pk=post_pk)
        except Post.DoesNotExist:
            raise Http404("Post does not exist.")

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post is None or request.user != post.author:
            return redirect('blog:post_detail', post_pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.POSTS_PER_PAGE

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            Q(is_published=True)
            & Q(category__is_published=True)
            & Q(pub_date__lte=timezone.now())
        ).annotate(comments_count=Count('comments')
                   ).order_by('-pub_date'
                              ).select_related('author', 'location', 'category')
        return queryset


class PostCreateView(LoginRequiredMixin, PostFormMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username}
                       )


class PostUpdateView(LoginRequiredMixin, PostFormMixin,
                     PostUpdateMixin, UpdateView):
    def get_success_url(self):
        post = self.object
        return reverse('blog:post_detail', kwargs={'post_pk': post.pk})


class PostDeleteView(LoginRequiredMixin, PostFormMixin,
                     PostUpdateMixin, DeleteView):
    success_url = reverse_lazy('blog:index')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        if 'post_pk' in self.kwargs:
            pk = self.kwargs['post_pk']
            post = get_object_or_404(Post, pk=pk)
        else:
            raise Http404("Не указан идентификатор объекта")
        if ((self.request.user != post.author)
            and ((not post.category.is_published)
                 or (not post.is_published))):
            raise Http404("Пост снят с публикации и доступен только автору")
        if post.pub_date > timezone.now() and self.request.user != post.author:
            raise Http404("Пост доступен только автору")
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(post=self.object)
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_pk': self.kwargs['post_pk']})


class CommentUpdateView(LoginRequiredMixin, CommentUpdateMixin, UpdateView):
    pass


class CommentDeleteView(LoginRequiredMixin, CommentUpdateMixin, DeleteView):
    pass


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = settings.POSTS_PER_PAGE

    def get_queryset(self):
        query_set = super().get_queryset()
        profile = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user != profile:
            query_set = query_set.filter(
                Q(is_published=True)
                & Q(pub_date__lte=timezone.now())
                ).annotate(comments_count=Count('comments')
                           ).order_by('-pub_date'
                                      ).select_related('author', 'location', 'category')
        else:
            query_set = query_set.filter(
                Q(author=self.request.user)
                ).annotate(comments_count=Count('comments')
                           ).order_by('-pub_date'
                                      ).select_related('author', 'location', 'category')
        return query_set

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_username = self.kwargs['username']
        context['profile'] = get_object_or_404(User, username=profile_username)
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ('username', 'first_name', 'last_name', 'email')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CategoryPostListView(ListView):
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = settings.POSTS_PER_PAGE
    category = None

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        return Post.objects.filter(
            Q(category__slug=category_slug)
            & Q(is_published=True)
            & Q(category__is_published=True)
            & Q(pub_date__lte=timezone.now())
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return context
