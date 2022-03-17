from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:

        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Group',
            'image': 'Картинка'
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка к посту'
        }

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('поле Text не должно быть пустым')

        return data


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == "":
            raise forms.ValidationError(
                'Вы обязательно должны заполнить поле!')
        return data
