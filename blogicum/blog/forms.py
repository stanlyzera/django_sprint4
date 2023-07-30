from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author', 'is_published', )
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',)
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
