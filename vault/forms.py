from django import forms
from .models import FamilyMember, Document, CATEGORY_CHOICES, FILE_TYPE_CHOICES


class DocumentUploadForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=FamilyMember.objects.all(),
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
            'placeholder': 'e.g. Aadhaar Card, CGHS Card…',
        }),
    )
    file_type = forms.ChoiceField(
        choices=FILE_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'type-radio'}),
        initial='image',
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'file-input', 'accept': '.jpg,.jpeg,.png,.pdf'}),
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
        max_size = 10 * 1024 * 1024  # 10 MB
        if f.size > max_size:
            raise forms.ValidationError("File too large. Maximum size is 10 MB.")
        allowed = ['.jpg', '.jpeg', '.png', '.pdf']
        ext = '.' + f.name.rsplit('.', 1)[-1].lower()
        if ext not in allowed:
            raise forms.ValidationError(f"Unsupported file type. Allowed: {', '.join(allowed)}")
        return f


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ['display_name', 'name', 'avatar_letter', 'avatar_color']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Papa, Mummy'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Rajesh Sharma'}),
            'avatar_letter': forms.TextInput(attrs={'class': 'form-input', 'maxlength': '2', 'placeholder': 'R'}),
            'avatar_color': forms.Select(attrs={'class': 'form-select'}),
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
