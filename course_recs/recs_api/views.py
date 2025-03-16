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
from django.core.exceptions import PermissionDenied


class UserRegisterView(CreateView):
    form_class = UserStudentRegistrationForm
    template_name = 'registration.html'
    success_url = reverse_lazy('login')


class CourseDetailView(DetailView):
    model = Course
    template_name = 'course.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            course = self.get_object()
            is_course_saved = UserCourse.objects.filter(user=user, course=course).exists()
            context['is_course_saved'] = is_course_saved

        return context


def UserCoursesView(request, user_id):
    courses = UserCourse.objects.filter(user=user_id).exclude(score=-1).exclude(score=-2)#, source='Native')
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
    user_course = get_object_or_404(UserCourse, user_id=user_id, course_id=pk)
    user_course.delete()
    messages.success(request, 'Курс успешно удален')
    return redirect(request.META.get('HTTP_REFERER', '/'))


def delete_course2(request, user_id, pk):
    user_course = get_object_or_404(UserCourse, user_id=user_id, course_id=pk)
    user_course.score = -1
    user_course.save()
    messages.success(request, 'Курс успешно удален')
    return redirect(request.META.get('HTTP_REFERER', '/'))


def delete_user(request, user_id):

    if not request.user.is_authenticated or (request.user.id != user_id and not request.user.is_staff):
        raise PermissionDenied("У вас нет прав для удаления этого аккаунта.")

    user = get_object_or_404(UserStudent, pk=user_id)
    user.delete()
    messages.success(request, 'Аккаунт успешно удален')
    return redirect(reverse('home'))


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


def create_user_courses_after_stepik_parser(user_courses, user):

    for course in user_courses:
        if not UserCourse.objects.filter(user=user, course=course[0]).exists():
            user_course = UserCourse(
                course=course[0],
                date_added=course[2],
                user=user,
                source='External',
                score=float(course[1] / 5)
            )
            user_course.save()
        else:
            continue


class CreateUserPlatformView(View):
    template_name = 'create_user_platform.html'

    def get(self, request, user_id):
        user = get_object_or_404(UserStudent, id=user_id)
        form = UserPlatformForm()
        return render(request, self.template_name, {'form': form, 'user': user})

    def post(self, request, user_id):

        user = get_object_or_404(UserStudent, id=user_id)
        form = UserPlatformForm(request.POST)
        if form.is_valid():
            platform = form.cleaned_data['platform']
            user_platform_id = form.cleaned_data['user_platform_id']

            if UserPlatform.objects.filter(user=user, platform=platform).exists():
                messages.error(request, 'Эта платформа уже привязана к вашему аккаунту.')
            else:
                existing_user_platform = UserPlatform.objects.filter(user_platform_id=user_platform_id).first()
                if existing_user_platform:
                    existing_user = existing_user_platform.user
                    existing_user.delete()

                user_platform = form.save(commit=False)
                user_platform.user = user  # Привязываем пользователя
                user_platform.save()

                user_platform_id = user_platform.user_platform_id
                #1031102530
                print('stert------------------------------')
                user_courses_to_add = fetch_reviewed_courses(user_platform_id)
                create_user_courses_after_stepik_parser(user_courses_to_add, user)
                print('finish--------------------------------')

                return redirect(reverse('profile', kwargs={'user_id': user_id}))
        return render(request, self.template_name, {'form': form, 'user': user})


class CreateUserCourseView(View):
    def get(self, request, course, user, score):
        user_student = get_object_or_404(UserStudent, id=user)
        course_obj = get_object_or_404(Course, id=course)

        # Проверяем, существует ли уже связь между пользователем и курсом
        # if UserCourse.objects.filter(user=user_student, course=course_obj).exists():
        #    return JsonResponse({'message': 'This user is already enrolled in this course.'}, status=400)

        user_course = UserCourse.objects.create(
            source='Native',
            user=user_student,
            course=course_obj,
            date_added=timezone.now(),
            score=float(score)
        )

        return redirect(request.META.get('HTTP_REFERER', '/'))


def custom_logout(request):
    logout(request)
    return redirect('home')


def HomeSortView3(request):
    courses = Course.objects.all()
    return render(request, 'home2.html', {'object_list': courses})


def HomeSortView(request):
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
    # courses = courses[:100]
    # Пагинация
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    filter_params = request.GET.copy()
    if 'page' in filter_params:
        del filter_params['page']  # Удаляем параметр 'page', чтобы он не дублировался

    # Получаем все платформы и уникальные категории для отображения в фильтре
    platforms = Platform.objects.all()
    categories = Course.objects.exclude(category__isnull=True).values_list('category', flat=True).distinct()

    return render(request, 'home2.html', {
        # 'courses': courses,
        'page_obj': page_obj,
        'platforms': platforms,
        'categories': categories,
        'selected_categories': selected_categories,
        'selected_platforms': selected_platforms,
        'search_query': search_query,
        'filter_params': filter_params.urlencode(),
        'get_not_all': False,
    })


def HomeSortView2(request):

    user = request.user
    if user.is_authenticated:

        recommended_courses_ids = Recommendations.objects.filter(user=user).values_list('recommended_courses',
                                                                                        flat=True).first()

        if recommended_courses_ids:
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

    filter_params = request.GET.copy()
    if 'page' in filter_params:
        del filter_params['page']  # Удаляем параметр 'page', чтобы он не дублировался

    # Получаем все платформы и уникальные категории для отображения в фильтре
    platforms = Platform.objects.all()
    categories = Course.objects.exclude(category__isnull=True).values_list('category', flat=True).distinct()

    return render(request, 'home2.html', {
        #'courses': courses,
        'page_obj': page_obj,
        'platforms': platforms,
        'categories': categories,
        'selected_categories': selected_categories,
        'selected_platforms': selected_platforms,
        'search_query': search_query,
        'filter_params': filter_params.urlencode(),
        'get_not_all': True,
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