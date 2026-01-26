from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile, VerificationCode
import random
import string

@api_view(['POST'])
def register(request):
    try:
        email = request.data.get('email')
        full_name = request.data.get('fullName')
        phone = request.data.get('phone')
        password = request.data.get('password')

        # Vérifier si l'email existe
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Cet email est déjà utilisé'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        # Créer le profil
        UserProfile.objects.create(user=user, phone=phone)

        # Générer et envoyer le code
        verification = VerificationCode.objects.create(email=email)
        code = verification.generate_code()
        verification.save()

        # Envoyer l'email
        send_verification_email(email, code, full_name)

        return Response(
            {'message': 'Code de vérification envoyé à votre email'},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def verify_code(request):
    try:
        email = request.data.get('email')
        code = request.data.get('code')

        # Vérifier le code
        verification = VerificationCode.objects.filter(
            email=email,
            code=code,
            is_used=False
        ).latest('created_at')

        if not verification:
            return Response(
                {'error': 'Code invalide ou expiré'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marquer comme utilisé
        verification.is_used = True
        verification.save()

        # Activer l'utilisateur
        user = User.objects.get(email=email)
        user_profile = UserProfile.objects.get(user=user)
        user_profile.is_verified = True
        user_profile.save()

        return Response(
            {'message': 'Email vérifié avec succès'},
            status=status.HTTP_200_OK
        )

    except VerificationCode.DoesNotExist:
        return Response(
            {'error': 'Code invalide'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

def send_verification_email(email, code, full_name):
    subject = 'Confirmez votre email - Search Home'
    message = f'''
Bienvenue {full_name} !

Votre code de vérification pour Search Home est :

{code}

Ce code expire dans 10 minutes.

Ne partagez ce code avec personne.

Cordialement,
L'équipe Search Home
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {str(e)}")