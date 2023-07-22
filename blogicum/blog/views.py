from typing import Any, Dict
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import redirect

class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            Q(is_published=True) &
            Q(category__is_published=True) & 
            Q(pub_date__lte=timezone.now()) 
        )
        queryset = queryset.annotate(comments_count=Count('comments'))
        queryset = queryset.order_by('-pub_date')
        return queryset

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    def get_success_url(self):
        post = self.object
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Post, pk=kwargs['pk'], author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post = self.object
        if not self.request.user.is_authenticated:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        return reverse('blog:post_detail', kwargs={'pk': post.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm 
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Post, pk=kwargs['pk'], author=request.user)
        return super().dispatch(request, *args, **kwargs)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

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
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm
    
    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs['comment_pk'])
        if comment.author != request.user:
            raise Http404("У вас нет прав для редактирования этого комментария")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post = self.object.post  
        return reverse('blog:post_detail', kwargs={'pk': post.pk})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs['comment_pk'])
        if comment.author != request.user:
            raise Http404("У вас нет прав для редактирования этого комментария")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post = self.object.post  
        return reverse('blog:post_detail', kwargs={'pk': post.pk})


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        posts = Post.objects.filter(author=user)
        paginator = Paginator(posts, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj  # Передаем объекты для пагинации в контекст
        posts_with_comments = Post.objects.filter(author=user).annotate(comments_count=Count('comments'))
        comment_count = sum([post.comments_count for post in posts_with_comments])

        for post in page_obj:
            post.comments_count = next((item.comments_count for item in posts_with_comments if item.pk == post.pk), 0)

        context['comment_count'] = comment_count
        return context
        
    
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'email']  
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})
        

class CategoryPostListView(ListView):
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        return Post.objects.filter(
            Q(category__slug=category_slug) & 
            Q(is_published=True) &
            Q(category__is_published=True) &  
            Q(pub_date__lte=timezone.now())  
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category, slug=self.kwargs['category_slug'], is_published=True)
        return context
