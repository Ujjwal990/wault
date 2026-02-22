from django import forms
from .models import FamilyMember, Document, CATEGORY_CHOICES, FILE_TYPE_CHOICES

ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']


class DocumentUploadForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['member'].queryset = FamilyMember.objects.filter(owner=user)

    member = forms.ModelChoiceField(
        queryset=FamilyMember.objects.none(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Aadhaar Card, Resume, CGHS Card…',
        }),
    )
    file_type = forms.ChoiceField(choices=FILE_TYPE_CHOICES, initial='image')
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': '.jpg,.jpeg,.png,.pdf,.doc,.docx',
        }),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 3,
            'placeholder': 'Optional notes about this document…',
        }),
    )

    def clean_file(self):
        f = self.cleaned_data['file']
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File too large. Maximum size is 10 MB.")
        ext = '.' + f.name.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                f"Unsupported file type. Allowed: JPG, PNG, PDF, DOC, DOCX."
            )
        return f


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ['display_name', 'name', 'avatar_letter', 'avatar_color', 'photo']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Papa, Mummy'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Rajesh Sharma'}),
            'avatar_letter': forms.TextInput(attrs={
                'class': 'form-input', 'maxlength': '3',
                'placeholder': 'e.g. RS (leave blank to auto-generate)',
            }),
            'avatar_color': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={'class': 'file-input', 'accept': 'image/*'}),
        }


class DocumentRenameForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'category', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
