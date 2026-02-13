from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailOrIdBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by email (case-insensitive)
            user = UserModel.objects.get(email__iexact=username)
        except UserModel.DoesNotExist:
            try:
                # Try to fetch the user by unique_id (case-sensitive)
                user = UserModel.objects.get(unique_id=username)
            except UserModel.DoesNotExist:
                # Neither email nor unique_id matched
                return None

        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
