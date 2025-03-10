from django.urls import path
from . import views
from .views import UserRegisterView, custom_logout, HomeSortView, CourseDetailView, UserCoursesView, \
    UserCourseDeleteView, HomeSortView2, UserCourseCreateView,  CreateUserCourseView, CreateUserPlatformView, \
    change_username, change_password, delete_course


urlpatterns = [
    path('', HomeSortView2, name='home'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('logout/', custom_logout, name='logout'),
    path('course/<int:pk>', CourseDetailView.as_view(), name="course"),
    path('user/<int:user_id>', UserCoursesView, name="profile"),
    path('user/<int:user_id>/<int:pk>/delete', delete_course, name='delete-course'),
    path('create/<int:course>/<int:user>/create', CreateUserCourseView.as_view(), name='create-usercourse'),
    path('user-platform/create/<int:user_id>/', CreateUserPlatformView.as_view(), name='create_user_platform'),
    path('change-username/', change_username, name='change-username'),
    path('change-password/', change_password, name='change-password'),
]
