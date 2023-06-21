from django.urls import path
from api import views

urlpatterns = [
  path('login/', views.api_login, name='api.login'),
  path('logout/', views.api_logout, name='api.logout'),
  path('signup/', views.api_signup, name='api.signup'),
  path('me/', views.api_me, name='api.me'),

  path('therapists/', views.api_therapists, name='api.therapists'),
  path('therapists/<id>/turns/', views.api_turns_by_therapist, name='api.therapists.turns'),

  path('turns/', views.api_turns, name='api.turns'),
  path('turns/<turn>/assign/', views.api_assign_turn, name='api.turns.assign'),

  path('reservations/', views.api_reservations, name='api.reservations'),
  path('reservations/export/', views.api_reservations_export, name='api.reservations.export'),
  path('reservations/<id>/', views.api_reservations_info, name='api.reservations.info'),

]
