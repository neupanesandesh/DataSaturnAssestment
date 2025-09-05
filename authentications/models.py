
from django.conf import settings
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import secrets


class APIKeyManager(models.Manager):
    def create_key(self, user, name=None):
        raw = secrets.token_urlsafe(32)
        hashed = make_password(raw)
        instance = self.create(user=user, name=name or "default", key_hash=hashed)
        return instance, raw

    def verify_key(self, raw_key):
        for instance in self.filter(revoked=False):
            if check_password(raw_key, instance.key_hash):
                return instance
        return None


class APIKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=100, blank=True, default="")
    key_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    objects = APIKeyManager()

    def mark_used(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])


class MFADevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mfa_devices")
    name = models.CharField(max_length=100, default="totp")
    secret = models.CharField(max_length=64)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
