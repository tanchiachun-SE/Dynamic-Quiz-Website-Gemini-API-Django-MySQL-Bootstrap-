from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('questions/', views.question_list, name='question_list'),
    path('questions/create/', views.question_create, name='question_create'),
    path('questions/y_n_create/',views.yes_no_create, name='yes_no_create'),
    path('questions/update/<int:qid>/', views.question_update, name='question_update'),
    path('questions/delete/<int:qid>/', views.question_delete, name='question_delete'),
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/update/<int:aid>/', views.assignment_update, name='assignment_update'),
    path('assignments/delete/<int:aid>/', views.assignment_delete, name='assignment_delete'),
    path('student/dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('student/exam/', views.student_exam_view, name='student_exam'),
    path('student/exam/take/<int:aid>/', views.take_exam_view, name='take_exam'),
    path('start-exam/<int:aid>', views.start_exam_view,name='start_exam'),
    path('random-exam/<int:aid>/', views.random_view, name='random_view'),
    path('fixed-exam/<int:aid>/', views.fixed_view, name='fixed_view'),
    path('dynamic_view/<int:aid>/', views.dynamic_view, name='dynamic_view'),
    path('student-results/', views.student_results, name='student_results'),
    path('student-result-detail/<int:result_id>/', views.student_result_detail, name='student_result_detail'),
    path('download/xlsm_s/', views.download_xlsm_s, name='download_xlsm_s'),
    path('download-result/<int:result_id>/', views.download_student_result_xlsm, name='download_student_result'),
    path('publish-assignment/<int:aid>/', views.publish_assignment, name='publish_assignment'),
    path('Ai_question_create/', views.Ai_question_create, name='Ai_question_create'),
    path('ai_yes_no_create/', views.Ai_yes_no_create, name='ai_yes_no_create'),


]