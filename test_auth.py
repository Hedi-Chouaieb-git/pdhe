import os
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Elearn.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model
from users.models import User

def test_authentication():
    """
    Script de diagnostic pour tester l'authentification des utilisateurs.
    """
    # Afficher tous les utilisateurs avec le rôle 'student'
    print("=== Liste des étudiants dans la base de données ===")
    students = User.objects.filter(role='student')
    
    if not students:
        print("Aucun étudiant trouvé dans la base de données.")
        return
    
    for student in students:
        print(f"ID: {student.id}, Email: {student.email}, Username: {student.username}")
    
    # Demander à l'utilisateur de saisir l'email et le mot de passe d'un étudiant
    print("\n=== Test d'authentification ===")
    email = input("Entrez l'email de l'étudiant: ")
    password = input("Entrez le mot de passe: ")
    
    # Tester l'authentification avec le backend par défaut
    user = authenticate(username=email, password=password)
    
    if user:
        print(f"\nAuthentification réussie!")
        print(f"Utilisateur: {user.email} (ID: {user.id})")
        print(f"Rôle: {user.get_role_display()}")
    else:
        print("\nÉchec de l'authentification.")
        
        # Vérifier si l'utilisateur existe
        try:
            user = User.objects.get(email=email)
            print(f"L'utilisateur avec l'email '{email}' existe dans la base de données.")
            print(f"ID: {user.id}, Username: {user.username}, Rôle: {user.get_role_display()}")
            print("Le problème vient probablement du mot de passe.")
        except User.DoesNotExist:
            print(f"Aucun utilisateur trouvé avec l'email '{email}'.")

if __name__ == "__main__":
    test_authentication()
