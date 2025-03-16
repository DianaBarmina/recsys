from .forms import UserStudentRegistrationForm, UserCourseForm, UserPlatformForm, UsernameChangeForm, \
    PasswordChangeCustomForm
from .models import UserStudent, Platform, Course, UserCourse, UserPlatform, Recommendations
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from django.utils import timezone
from django.http import JsonResponse
from django.views import View
from .parsing.stepic import fetch_reviewed_courses
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator



#def home(request):
#    return render(request, 'home.html', {})


class UserRegisterView(CreateView):
    form_class = UserStudentRegistrationForm
    template_name = 'registration.html'
    success_url = reverse_lazy('login')


class CourseDetailView(DetailView):
    model = Course
    template_name = 'course.html'

    def get_context_data(self, **kwargs):
        # Получаем контекст по умолчанию
        context = super().get_context_data(**kwargs)

        # Получаем текущего пользователя (UserStudent)
        user = self.request.user

        # Проверяем, авторизован ли пользователь и является ли он UserStudent
        if user.is_authenticated:
            # Проверяем, добавлен ли курс в сохраненные (UserCourse)
            course = self.get_object()  # Получаем текущий курс
            is_course_saved = UserCourse.objects.filter(user=user, course=course).exists()
            context['is_course_saved'] = is_course_saved

        return context


def UserCoursesView(request, user_id):
    courses = UserCourse.objects.filter(user=user_id).exclude(score=-1)#, source='Native')
    course = []
    for i in range(len(courses)):
        course.append(courses[i].course.pk)
    user_courses = Course.objects.filter(pk__in=course).order_by('date_added')
    user = get_object_or_404(UserStudent, pk=user_id)

    user_platforms = UserPlatform.objects.filter(user=user_id)
    u_platform = []
    for i in range(len(user_platforms)):
        u_platform.append(user_platforms[i].platform.pk)
    platforms = Platform.objects.filter(pk__in=u_platform)

    paginator = Paginator(user_courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'profile2.html', {'courses': user_courses,
                                             'user': user,
                                             'platforms': platforms,
                                             'page_obj': page_obj
                                             })


def delete_course(request, user_id, pk):
    # Получаем курс пользователя
    user_course = get_object_or_404(UserCourse, user_id=user_id, course_id=pk)
    user_course.delete()
    messages.success(request, 'Курс успешно удален')
    #return redirect(reverse('profile', kwargs={'user_id': user_id}))
    return redirect(request.META.get('HTTP_REFERER', '/'))


def delete_course2(request, user_id, pk):
    # Получаем курс пользователя
    user_course = get_object_or_404(UserCourse, user_id=user_id, course_id=pk)
    user_course.score = -1
    user_course.save()
    messages.success(request, 'Курс успешно удален')
    return redirect(request.META.get('HTTP_REFERER', '/'))


class UserCourseDeleteView(DeleteView):
    model = UserCourse
    template_name = 'delete_course.html'

    def get_success_url(self):
        return reverse('profile', kwargs={'user_id': self.request.user.pk})


class UserCourseCreateView(CreateView):
    model = UserCourse
    form_class = UserCourseForm
    template_name = None

    def get_success_url(self):
        return reverse('home', kwargs={'user_id': self.request.user.pk})

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.course = Course.objects.get(pk=self.kwargs['course'])
        form.instance.source = 'Native'
        form.instance.date_added = timezone.now()
        form.instance.score = 5

        if UserCourse.objects.filter(user=self.request, course=self.kwargs['course']).exists():
            return JsonResponse({'error': 'UserCourse already exists'}, status=400)

        self.object = form.save()

        return super().form_valid(form)


class CreateUserPlatformView(View):
    template_name = 'create_user_platform.html'  # Укажите шаблон

    def get(self, request, user_id):
        # Получаем пользователя на основе переданного user_id
        user = get_object_or_404(UserStudent, id=user_id)

        # Создаем пустую форму с привязкой к пользователю
        form = UserPlatformForm()
        return render(request, self.template_name, {'form': form, 'user': user})

    def post(self, request, user_id):
        # Получаем пользователя на основе переданного user_id
        user = get_object_or_404(UserStudent, id=user_id)

        # Заполняем форму данными из POST-запроса
        form = UserPlatformForm(request.POST)
        if form.is_valid():

            platform = form.cleaned_data['platform']  # Получаем платформу из формы

            user_platform_id = form.cleaned_data['user_platform_id']

            # Проверяем, существует ли уже запись с таким пользователем и платформой
            if UserPlatform.objects.filter(user=user, platform=platform).exists():
                # Если запись уже существует, добавляем сообщение об ошибке
                # form.add_error('platform', 'Эта платформа уже привязана к вашему аккаунту.')
                messages.error(request, 'Эта платформа уже привязана к вашему аккаунту.')
            else:
                existing_user_platform = UserPlatform.objects.filter(user_platform_id=user_platform_id).first()
                if existing_user_platform:
                    # Удаляем пользователя и все его связи каскадно
                    existing_user = existing_user_platform.user
                    existing_user.delete()

                # Создаем объект UserPlatform, но не сохраняем его в базу
                user_platform = form.save(commit=False)
                user_platform.user = user  # Привязываем пользователя

                user_platform.save()  # Сохраняем объект в базе

                user_platform_id = user_platform.user_platform_id
                #1031102530
                print('stert------------------------------')
                print(fetch_reviewed_courses(user_platform_id))
                print('finish--------------------------------')

                return redirect(reverse('profile', kwargs={'user_id': user_id}))# Перенаправляем на страницу успеха (замените на вашу)
        return render(request, self.template_name, {'form': form, 'user': user})


class CreateUserCourseView(View):
    def get(self, request, course, user):
        # Получаем объекты UserStudent и Course
        user_student = get_object_or_404(UserStudent, id=user)
        course_obj = get_object_or_404(Course, id=course)

        # Проверяем, существует ли уже связь между пользователем и курсом
        if UserCourse.objects.filter(user=user_student, course=course_obj).exists():
            return JsonResponse({'message': 'This user is already enrolled in this course.'}, status=400)

        # Создаем новую запись UserCourse
        user_course = UserCourse.objects.create(
            source='Native',  # Укажите значение по умолчанию для поля `source`
            user=user_student,
            course=course_obj,
            date_added=timezone.now(),
            score=5
        )

        return redirect(request.META.get('HTTP_REFERER', '/'))

        # Возвращаем успешный ответ
        '''return JsonResponse({
            'message': 'UserCourse created successfully!',
            'user_course_id': user_course.id
        })'''


def custom_logout(request):
    logout(request)
    return redirect('home')  # Перенаправление на главную страницу


def HomeSortView(request):
    #flights = Course.objects.filter(departure_time__date__gt=datetime.now().date()).order_by('departure_time')
    courses = Course.objects.all()
    return render(request, 'home.html', {'object_list': courses})


def HomeSortView2(request):
    # Получаем все курсы с аннотацией и сортировкой
    user = request.user
    if user.is_authenticated:

        recommended_courses_ids = Recommendations.objects.filter(user=user).values_list('recommended_courses',
                                                                                        flat=True).first()

        if recommended_courses_ids:
            # Если есть рекомендации, выбираем курсы по их ID
            courses = Course.objects.filter(id__in=recommended_courses_ids)
        else:
            # Если рекомендаций нет, выбираем топ-100 популярных курсов
            courses = Course.objects.annotate(student_count=Count('usercourse')).order_by('-student_count')

        saved_courses = UserCourse.objects.filter(user=user).exclude(score=-1).values_list('course_id', flat=True)
        courses = courses.exclude(id__in=saved_courses)
    else:
        courses = Course.objects.all()

    # Фильтрация по нескольким категориям
    selected_categories = request.GET.getlist('category')
    selected_platforms = request.GET.getlist('platform')
    search_query = request.GET.get('search', '')

    # Обрабатываем сброс фильтров
    reset_filters = request.GET.get('reset')
    if reset_filters:
        selected_categories = []
        selected_platforms = []
        search_query = ''

    # Применяем фильтрацию, если фильтры не сброшены
    if selected_categories:
        courses = courses.filter(category__in=selected_categories)

    if selected_platforms:
        courses = courses.filter(platform_id__in=selected_platforms)

    if search_query:
        courses = courses.filter(title__icontains=search_query)
    # Применяем срез только после всех фильтров
    #courses = courses[:100]
        # Пагинация
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Получаем все платформы и уникальные категории для отображения в фильтре
    platforms = Platform.objects.all()
    categories = Course.objects.exclude(category__isnull=True).values_list('category', flat=True).distinct()
    # Передаем данные в шаблон
    return render(request, 'home2.html', {
        #'courses': courses,
        'page_obj': page_obj,
        'platforms': platforms,
        'categories': categories,
        'selected_categories': selected_categories,
        'selected_platforms': selected_platforms,
        'search_query': search_query,
    })


@login_required
def change_username(request):
    if request.method == 'POST':
        form = UsernameChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Имя пользователя успешно изменено!')
            return redirect('profile', user_id=request.user.id)
    else:
        form = UsernameChangeForm(instance=request.user)
    return render(request, 'profile2.html', {'username_form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Обновляем сессию, чтобы пользователь не вышел из системы
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('profile', user_id=request.user.id)
    else:
        form = PasswordChangeCustomForm(request.user)
    return render(request, 'profile2.html', {'password_form': form})