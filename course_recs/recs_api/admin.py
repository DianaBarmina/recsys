from django.contrib import admin
from .models import UserStudent, UserCourse, UserPlatform, Platform, Course, Recommendations
# Register your models here.

admin.site.register(UserStudent)
admin.site.register(Platform)
admin.site.register(Course)
admin.site.register(UserPlatform)
admin.site.register(UserCourse)
admin.site.register(Recommendations)