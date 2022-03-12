from posts.models import Post, Comment
from django import forms


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = "Группа не выбрана"
        self.fields['group'].widget.attrs.update({'class': 'form-control'})
        self.fields['text'].widget.attrs.update({'class': ' form-control'})

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')


class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].empty_label = "введите текст"
        self.fields['text'].widget.attrs.update({'class': ' form-control'})

    class Meta:
        model = Comment
        fields = ('text',)
