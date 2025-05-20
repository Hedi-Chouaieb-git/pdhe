import os
import django
import random
import string

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Elearn.settings')
django.setup()

from users.models import User

def generate_password(length=10):
    """Génère un mot de passe aléatoire"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    return ''.join(random.choice(chars) for _ in range(length))

def reset_student_passwords():
    """Réinitialise les mots de passe de tous les étudiants"""
    students = User.objects.filter(role='student')
    
    if not students:
        print("Aucun étudiant trouvé dans la base de données.")
        return
    
    print(f"Réinitialisation des mots de passe pour {students.count()} étudiants...")
    
    for student in students:
        # Générer un nouveau mot de passe
        new_password = generate_password()
        
        # Définir le nouveau mot de passe
        student.set_password(new_password)
        student.save()
        
        print(f"Étudiant: {student.email}")
        print(f"Nouveau mot de passe: {new_password}")
        print("-" * 50)
    
    print("Réinitialisation des mots de passe terminée.")

if __name__ == "__main__":
    reset_student_passwords()
