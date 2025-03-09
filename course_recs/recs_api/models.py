from django.db import models
from django.contrib.auth.models import AbstractUser


class Platform(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=False)
    users = models.ManyToManyField('UserStudent', through='UserPlatform')

    def __str__(self):
        return self.name


class UserStudent(AbstractUser):
    platforms = models.ManyToManyField('Platform', through='UserPlatform')
    courses = models.ManyToManyField('Course', through='UserCourse')


class UserPlatform(models.Model):
    user_platform_id = models.IntegerField()
    user = models.ForeignKey('UserStudent', on_delete=models.CASCADE)
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)


class Course(models.Model):
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE)
    platform_course_id = models.IntegerField(null=True)
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=255, null=True)
    workload = models.CharField(max_length=255, null=True)
    canonical_url = models.URLField(blank=True, null=False)
    summary = models.TextField(null=True)
    description = models.TextField(null=True)
    became_published_at = models.DateTimeField()
    time_to_complete = models.IntegerField(null=True)
    is_paid = models.BooleanField()
    category = models.CharField(max_length=255, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    #image = models.

    courses = models.ManyToManyField('UserStudent', through='UserCourse')

    def __str__(self):
        return self.title


class GetSource(models.TextChoices):
    NATIVE = "Native", "Native"
    EXTERNAL = "External", "External"


class UserCourse(models.Model):

    source = models.CharField(
        max_length=8,
        choices=GetSource.choices
    )

    user = models.ForeignKey('UserStudent', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)  # всегда дата добавления в сервис
    score = models.IntegerField(default=5)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(source__in=[choice[0] for choice in GetSource.choices]),
                name='valid_source_check',
            ),
        ]

