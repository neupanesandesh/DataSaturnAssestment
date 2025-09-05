# auth_app/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import APIKey, MFADevice
from django.utils.translation import gettext_lazy as _
import pyotp


class MultiAuthBackend(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_API_KEY")
        if not api_key:
            return None 

        api_obj = APIKey.objects.verify_key(api_key)
        if not api_obj or api_obj.revoked:
            raise exceptions.AuthenticationFailed(_("Invalid API Key"))
        user = api_obj.user
        api_obj.mark_used()

        if self._mfa_required(user, request):
            raise exceptions.AuthenticationFailed(_("MFA required"))

        return (user, None)

    def _mfa_required(self, user, request) -> bool:
        devices = MFADevice.objects.filter(user=user, confirmed=True)
        if not devices.exists():
            return False
        code = request.META.get("HTTP_X_MFA_CODE")
        if not code:
            return True
        for d in devices:
            totp = pyotp.TOTP(d.secret)
            if totp.verify(code, valid_window=1):
                return False
        return True
