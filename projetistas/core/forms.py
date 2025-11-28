from django.contrib.auth.forms import SetPasswordForm

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = (
            "Sua senha não pode ser muito parecida com suas outras informações pessoais.<br>"
            "Sua senha deve conter pelo menos 8 caracteres.<br>"
            "Sua senha não pode ser uma senha comumente usada.<br>"
            "Sua senha não pode ser totalmente numérica."
        )