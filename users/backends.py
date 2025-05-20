from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(email=username) | Q(username=username)
            )
            print(password)
            if user.check_password(password):
                return user
            else:
                print(f"Mot de passe incorrect pour l'utilisateur: {username}")
                return None

        except User.DoesNotExist:
            # Aucun utilisateur trouvé avec cet email ou nom d'utilisateur
            print(f"Aucun utilisateur trouvé avec l'identifiant: {username}")
            return None
        except User.MultipleObjectsReturned:
            # Plusieurs utilisateurs trouvés (cas rare mais possible)
            # Dans ce cas, on prend le premier qui correspond au mot de passe
            users = User.objects.filter(
                Q(email=username) | Q(username=username)
            )
            for user in users:
                if user.check_password(password):
                    return user
            return None
