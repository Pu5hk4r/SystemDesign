from django.db import models
import random
import string

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class URL(models.Model):
    original_url = models.URLField()
    short_code = models.CharField(max_length = 10, unique = True)
    clicks = models.IntegerField(default = 0)
    is_active = models.BooleanField(default = True)
    created_at = models.DateTimeField(auto_now_add = True)
    custom_code = models.CharField(
        max_length = 20,
        unique = True,
        null = True,
        blank = True
        )
    
    def save(self, *args, **kwargs):
        if self.custom_code:
            self.short_code = self.custom_code
        elif not self.short_code:
            self.short_code = generate_short_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.short_code


