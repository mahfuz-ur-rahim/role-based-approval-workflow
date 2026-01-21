from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'content']
        widgets = {
            'content': SummernoteWidget(),
        }
