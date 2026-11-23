from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import EMAIL_MAX_LENGTH


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    email = models.EmailField(
        'Электронная почта',
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True,
        default='',
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_user_following',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} → {self.following.username}'
