from django import forms
from django_summernote.widgets import SummernoteWidget
from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'content']
        widgets = {
            'content': SummernoteWidget(
                attrs={
                    "summernote": {
                        "width": "100%",
                        "height": 400,
                        "toolbar": [
                            ["style", ["style"]],
                            ["font", ["bold", "italic", "underline", "clear"]],
                            ["fontsize", ["fontsize"]],
                            ["color", ["color"]],
                            ["para", ["ul", "ol", "paragraph"]],
                            ["insert", ["link", "picture", "table"]],
                            ["view", ["fullscreen", "codeview"]],
                        ],
                    }
                }
            ),
        }
