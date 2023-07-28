from django.http import Http404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q

from .forms import PostForm, CommentForm
from .models import Post, Category, Comment
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
            raise Http404("You don't have permission to edit this comment.")
        return comment

    def get_success_url(self):
        post = self.object.post
        return reverse('blog:post_detail', kwargs={'post_pk': post.pk})

    def handle_no_permission(self):
        post_pk = self.kwargs.get('post_pk')
        return redirect('blog:post_detail', post_pk=post_pk)


class PostUpdateDeleteMixin:
    pk_url_kwarg = 'post_pk'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_pk=post.pk)
        return super().dispatch(request, *args, **kwargs)


class QuerySetOptimizationMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author', 'location', 'category')
        return queryset


class PostListView(QuerySetOptimizationMixin, ListView):
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
                   ).order_by('-pub_date')
        return queryset


class PostCreateView(LoginRequiredMixin, PostFormMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(
    LoginRequiredMixin,
    PostFormMixin,
    PostUpdateDeleteMixin,
    UpdateView
):
    def get_success_url(self):
        post = self.object
        return reverse('blog:post_detail', kwargs={'post_pk': post.pk})


class PostDeleteView(
    LoginRequiredMixin,
    PostFormMixin,
    PostUpdateDeleteMixin,
    DeleteView
):
    success_url = reverse_lazy('blog:index')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_pk'

    def get_object(self, queryset=None):
        post = super().get_object(queryset=queryset)
        if ((self.request.user != post.author)
            and ((not post.category.is_published)
                 or (not post.is_published)
                 or (post.pub_date > timezone.now()))):
            raise Http404('Пост снят с публикации и доступен только автору')
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.all()
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
        return reverse(
            'blog:post_detail',
            kwargs={'post_pk': self.kwargs['post_pk']}
        )


class CommentUpdateView(LoginRequiredMixin, CommentUpdateMixin, UpdateView):
    pass


class CommentDeleteView(LoginRequiredMixin, CommentUpdateMixin, DeleteView):
    pass


class ProfileListView(QuerySetOptimizationMixin, ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = settings.POSTS_PER_PAGE
    profile = None

    def get_queryset(self):
        query_set = super().get_queryset()
        self.profile = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        query_set = query_set.filter(
            author=self.profile
        ).annotate(comments_count=Count('comments')
                   ).order_by('-pub_date')
        if self.request.user != self.profile:
            query_set = query_set.filter(
                Q(is_published=True)
                & Q(pub_date__lte=timezone.now())
            )
        return query_set

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
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


class CategoryPostListView(QuerySetOptimizationMixin, ListView):
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = settings.POSTS_PER_PAGE
    category = None

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return Post.objects.filter(
            Q(category__slug=category_slug)
            & Q(is_published=True)
            & Q(category__is_published=True)
            & Q(pub_date__lte=timezone.now())
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
