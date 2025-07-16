from django import forms
from .models import CustomUser


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your password",
            }
        )
    )


class StaffCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ["full_name", "email", "phone", "access_level", "branch"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password and confirm password do not match.")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(StaffCreationForm, self).__init__(*args, **kwargs)

        # Style form fields
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

        # Manager can't assign admin or manager level
        if user and user.access_level == "manager":
            self.fields["access_level"].choices = [
                choice
                for choice in CustomUser.ACCESS_LEVEL_CHOICES
                if choice[0] not in ["admin", "manager"]
            ]
            # Hide branch field from manager
            self.fields.pop("branch", None)


class StaffEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["full_name", "email", "phone", "access_level"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(StaffEditForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

        if user and user.access_level == "manager":
            self.fields["access_level"].choices = [
                choice
                for choice in CustomUser.ACCESS_LEVEL_CHOICES
                if choice[0] not in ["admin", "manager"]
            ]
