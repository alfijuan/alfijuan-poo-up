from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type_id = models.CharField(max_length=4, choices=settings.USER_CHOICES, default=settings.USER_CHOICES[0][0])
    dni = models.CharField(max_length=1000, default='', blank=True)
    pathology = models.CharField(max_length=1000, default='', blank=True)
    turn_time = models.CharField(max_length=2, choices=settings.THERAPIST_TURNS)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def to_json(self):
        obj = {
            'id': self.user.id,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }

        if self.type_id == "0000":
            return {
                **obj,
                'dni': self.dni if self.dni else '',
                'pathology': self.pathology
            }

        if self.type_id == "2002":
            return {
                **obj,
                'turn_time': self.turn_time,
            }
        
        return obj
    
class Turn(models.Model):
    start_time = models.DateTimeField(auto_now=False, null=True, blank=True)
    end_time = models.DateTimeField(auto_now=False, null=True, blank=True)
    available = models.BooleanField(default=True)
    therapist = models.ForeignKey(User, on_delete=models.CASCADE)

    def to_json(self):
        obj = {
            'id': self.id,
            'start_time': self.start_time.strftime("%d/%m/%y %H:%M:%S") if self.start_time else '',
            'end_time': self.end_time.strftime("%d/%m/%y %H:%M:%S") if self.end_time else '',
            'therapist': self.therapist.id,
            'available': self.available
        }
        
        return obj

class Reservation(models.Model):
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    pacient = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=1000, default='', blank=True)

    def to_json(self):
        obj = {
            'id': self.id,
            'turn': self.turn.id,
            'pacient': self.pacient.id,
            'status': self.status,
        }
        return obj 
