from django import forms
from django.forms import Textarea,RadioSelect
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from . import models
from django.core import signing

class ProfileForm(UserCreationForm):
    about = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2')

class RatingForm(forms.ModelForm):
    # if user1.canRate = 1 and edit if canEdit = 1
    #rating = forms.IntegerField(widget=forms.NumberInput(attrs={'class':'form-control adjust-size'}))
    #review = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control adjust-size'}))

    class Meta:
        choices=[]
        for i in range(1,11):
            curr_choice=(i,i) #Do remember that 'en' is the encryption of the TUPLE
            choices.append(curr_choice)

        model = models.Rating
        # fields = ('user1', 'user2', 'rating')
        fields = ('rating', 'review' )
        widgets={
        'rating':RadioSelect(choices=choices),
        'review': Textarea(attrs={'class':'form-control','rows':5,'cols':40})
        }
        labels={
        'rating':'Rating'
        }


class WorkForm(forms.ModelForm):
    #work = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control','rows':5,'cols':40}))

    #class Meta:
    #    model = models.Work
    #    fields = ('work', )
    class Meta:
        model = models.Work
        fields = ('work',)#,'choices_to_Delete')#,'Add_or_Delete')
        widgets={'work': Textarea(attrs={'class':'form-control','rows':5,'cols':40})}
        labels= { 'work': 'Write the work:' }
        help_texts={'work':'When using delete, write the work to be deleted.'}
        error_message={'work':'ERROR!'}

class UserUpdateForm(forms.Form):
    about = forms.CharField(initial='about',widget=forms.Textarea(attrs={'class':'form-control','rows':5,'cols':40}))

    class Meta:
        model = models.Profile
        fields = ('about', )

class LoginForm(forms.Form):
    userid = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))

class SudoForm(forms.ModelForm):

    class Meta:
        model = models.Control
        fields = ('SessionNumber', 'RegistrationEnabled' , 'EveryoneCanSee', 'EveryoneCanRate', 'EveryoneCanEdit', 'UpdateEveryone' )
