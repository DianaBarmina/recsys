from django.urls import path
from . import views
from .views import UserRegisterView, custom_logout, HomeSortView, CourseDetailView, UserCoursesView, \
    UserCourseDeleteView, HomeSortView2, UserCourseCreateView,  CreateUserCourseView, CreateUserPlatformView, \
    change_username, change_password, delete_course2, delete_user


urlpatterns = [
    path('', HomeSortView2, name='home'),
    path('all-courses/', HomeSortView, name='all-courses'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('logout/', custom_logout, name='logout'),
    path('course/<int:pk>', CourseDetailView.as_view(), name="course"),
    path('user/<int:user_id>', UserCoursesView, name="profile"),
    path('user/<int:user_id>/<int:pk>/delete', delete_course2, name='delete-course'),
    path('create/<int:course>/<int:user>/<str:score>/create', CreateUserCourseView.as_view(), name='create-usercourse'),
    path('user-platform/create/<int:user_id>/', CreateUserPlatformView.as_view(), name='create_user_platform'),
    path('change-username/', change_username, name='change-username'),
    path('change-password/', change_password, name='change-password'),
    path('user/<int:user_id>/delete_account/', delete_user, name='delete_user')
]
