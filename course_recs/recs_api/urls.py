from django.urls import path
from . import views
from .views import UserRegisterView, custom_logout, HomeSortView, CourseDetailView, UserCoursesView, \
    UserCourseDeleteView, HomeSortView2, UserCourseCreateView,  CreateUserCourseView, CreateUserPlatformView


urlpatterns = [
    #path('', HomeSortView, name='home'),
    path('', HomeSortView2, name='home'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('logout/', custom_logout, name='logout'),
    path('course/<int:pk>', CourseDetailView.as_view(), name="course"),
    path('user/<int:user_id>', UserCoursesView, name="profile"),
    path('user/<int:user_id>/<int:pk>/delete', UserCourseDeleteView.as_view(), name='delete-course'),
    #path('create/<int:course>/<int:user>/create', UserCourseCreateView.as_view(), name='create-usercourse'),
    #path('create/<int:course>/<int:user>/create', create_user_course, name='create-usercourse'),
    path('create/<int:course>/<int:user>/create', CreateUserCourseView.as_view(), name='create-usercourse'),
    path('user-platform/create/<int:user_id>/', CreateUserPlatformView.as_view(), name='create_user_platform'),
]
