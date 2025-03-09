from .forms import UserStudentRegistrationForm, UserCourseForm, UserPlatformForm, UserStudentUpdateForm, UserStudentPasswordChangeForm
from .models import UserStudent, Platform, Course, UserCourse, UserPlatform
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from django.utils import timezone
from django.http import JsonResponse
from django.views import View
from .parsing.stepic import fetch_reviewed_courses


#def home(request):
#    return render(request, 'home.html', {})


class UserRegisterView(CreateView):
    form_class = UserStudentRegistrationForm
    template_name = 'registration.html'
    success_url = reverse_lazy('login')


class CourseDetailView(DetailView):
    model = Course
    template_name = 'course.html'


def UserCoursesView(request, user_id):
    courses = UserCourse.objects.filter(user=user_id, source='Native')
    course = []
    for i in range(len(courses)):
        course.append(courses[i].course.pk)
    user_courses = Course.objects.filter(pk__in=course)
    user = get_object_or_404(UserStudent, pk=user_id)
    return render(request, 'profile.html', {'courses': user_courses, 'user': user})


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
            # Создаем объект UserPlatform, но не сохраняем его в базу
            user_platform = form.save(commit=False)
            user_platform.user = user  # Привязываем пользователя
            user_platform.save()  # Сохраняем объект в базе

            print('start----------------------------------')
            user_platform_id = user_platform.user_platform_id
            print(fetch_reviewed_courses(user_platform_id))
            print('end--------------------------------------')

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
    # Получаем все курсы
    courses = Course.objects.all()

    # Фильтрация по нескольким категориям
    selected_categories = request.GET.getlist('category')  # Получаем список выбранных категорий
    if selected_categories:
        courses = courses.filter(category__in=selected_categories)  # Фильтруем по списку категорий

    # Фильтрация по нескольким платформам
    selected_platforms = request.GET.getlist('platform')  # Получаем список выбранных платформ
    if selected_platforms:
        courses = courses.filter(platform_id__in=selected_platforms)  # Фильтруем по списку платформ

    # Поиск по названию курса
    search_query = request.GET.get('search')
    if search_query:
        courses = courses.filter(title__icontains=search_query)

    # Получаем все платформы и уникальные категории для отображения в фильтре
    platforms = Platform.objects.all()
    categories = Course.objects.values_list('category', flat=True).distinct()  # Уникальные категории

    # Передаем данные в шаблон
    return render(request, 'home2.html', {
        'courses': courses,
        'platforms': platforms,
        'categories': categories,
        'selected_categories': selected_categories,
        'selected_platforms': selected_platforms,
        'search_query': search_query,
    })


'''@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserStudentUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserStudentUpdateForm(instance=request.user)
    return render(request, 'update_profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = UserStudentPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('profile')
    else:
        form = UserStudentPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})
'''