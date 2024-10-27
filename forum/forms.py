from django import forms
from .models import Article, Comment, Question, Answer

class ArticleForm(forms.ModelForm):
    remove_thumbnail = forms.BooleanField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Article
        fields = ['title', 'content', 'thumbnail_file', 'remove_thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'thumbnail_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        thumbnail_file = self.files.get('thumbnail_file')
        remove_thumbnail = cleaned_data.get('remove_thumbnail')

        if remove_thumbnail:
            cleaned_data['thumbnail_file'] = None
            return cleaned_data

        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'question']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }
