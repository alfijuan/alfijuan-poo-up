import json
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode

def get_request_body(request):
    return json.loads(request.body.decode('utf-8'))

def get_user(uidb64):
	try:
		# urlsafe_base64_decode() decodes to bytestring
		uid = urlsafe_base64_decode(uidb64).decode()
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist, ValidationError):
		user = None
	return user