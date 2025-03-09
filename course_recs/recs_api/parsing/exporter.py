import pandas as pd
import os
import django
import sys

# Добавляем путь к проекту в sys.path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_path)

# Указываем Django, какие настройки использовать
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recs.settings')  # Замените `course_recs` на имя вашего проекта

# Инициализация Django
django.setup()

from django.utils import timezone
from recs_api.models import Course, Platform, UserStudent, UserPlatform, UserCourse


def export_courses(df):
    for i in range(len(df)):
        title = df.iat[i, df.columns.get_loc('title')]
        language = df.iat[i, df.columns.get_loc('language')]
        workload = df.iat[i, df.columns.get_loc('workload')]
        canonical_url = df.iat[i, df.columns.get_loc('canonical_url')]
        summary = df.iat[i, df.columns.get_loc('summary')]
        description = df.iat[i, df.columns.get_loc('description')]
        became_published_at = df.iat[i, df.columns.get_loc('became_published_at')]
        time_to_complete = df.iat[i, df.columns.get_loc('time_to_complete')]
        is_paid = df.iat[i, df.columns.get_loc('is_paid')]
        category = df.iat[i, df.columns.get_loc('category')]
        platform_course_id = df.iat[i, df.columns.get_loc('stepik_course_id')]

        if pd.isna(workload):
            workload = None  # Устанавливаем значение NULL для базы данных

        if pd.isna(summary):
            summary = None  # Устанавливаем значение NULL для базы данных

        if pd.isna(description):
            description = None  # Устанавливаем значение NULL для базы данных

        if pd.isna(time_to_complete):
            time_to_complete = None  # Устанавливаем значение NULL для базы данных

        if pd.isna(category):
            category = None  # Устанавливаем значение NULL для базы данных

        # if pd.isna(cover):
        #    cover = None  # Устанавливаем значение NULL для базы данных


        # image = df.iat[i, 'cover']

        platform, created = Platform.objects.get_or_create(name='Stepik')

        course = Course(
            platform=platform,
            platform_course_id=platform_course_id,
            title=title,
            language=language,
            workload=workload,
            canonical_url=canonical_url,
            summary=summary,
            description=description,
            became_published_at=became_published_at,
            time_to_complete=time_to_complete,
            is_paid=is_paid,
            category=category,
            date_added=timezone.now(),
        )

        course.save()


def export_users(df):

    unique_users = df['stepik_user_id'].unique().tolist()

    for i in unique_users:
        username = f'student{i}'
        password = f'qwertyst{i}'
        user = UserStudent(
            username=username,
            password=password
        )

        user.save()

        platform, created = Platform.objects.get_or_create(name='Stepik')

        user_platform = UserPlatform(
            user_platform_id=i,
            user=user,
            platform=platform,
            date_added=timezone.now(),
        )

        user_platform.save()

        user_courses = df[df['stepik_user_id'] == i]

        for j in range(len(user_courses)):
            try:
                course_created, created1 = Course.objects.get_or_create(
                    platform_course_id=user_courses.iat[j, df.columns.get_loc('stepik_course_id')]
                )

                user_course = UserCourse(
                    course=course_created,
                    date_added=timezone.now(),
                    user=user,
                    source='External',
                    score=user_courses.iat[j, df.columns.get_loc('score')]
                )

                user_course.save()
            except:
                continue


if __name__ == "__main__":
    courses = pd.read_csv('df/courses_export.csv')
    export_courses(courses)

    reviews = pd.read_csv('df/reviews_export.csv')
    reviews['score'] /= 5
    export_users(reviews)
