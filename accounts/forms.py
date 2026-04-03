from django import forms
from django.forms import fields
from . import models

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = models.Assignment
        fields =  "__all__"

class QuestionBankForm(forms.ModelForm):
    class Meta:
        model = models.Questionbank
        fields =  "__all__"

class StudentAnswerForm(forms.ModelForm):
    class Meta:
        model = models.StudentAnswer
        fields =  "__all__"

class StudentResultForm(forms.ModelForm):
    class Meta:
        model = models.StudentResult
        fields =  "__all__"



class CustomQuestionBankForm(forms.ModelForm):

    class Meta:
        model = models.Questionbank
        fields =  "__all__"

    def __init__(self, *args, **kwargs):
        super(CustomQuestionBankForm, self).__init__(*args, **kwargs)
        # Limit the choices for the answer field to only Option 1 and Option 2
        self.fields['answer'].choices = [('Option1', 'Option1'), ('Option2', 'Option2')]

