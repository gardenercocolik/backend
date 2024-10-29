# backend/apps/dashboard/urls.py

from django.urls import path
from .views import ReportListView, RecordListView, ReportCreateView, RecordSubmitView, ReturnCompetitionNameView, GetUserInfoView, UpdateUserInfoView



urlpatterns = [
    path('reports/', ReportListView.as_view(), name='report-list'),
    path('records/', RecordListView.as_view(), name='record-list'),
    path('reports/create/', ReportCreateView.as_view(), name='report-create'),
    path('records/submit/', RecordSubmitView.as_view(), name='record-submit'),
    path('reports/return-competition-name/', ReturnCompetitionNameView.as_view(), name='return-competition-name'),
    path('userinfo/', GetUserInfoView.as_view(), name = "userinfo"),
    path('userinfo/update/', UpdateUserInfoView.as_view(), name = "updateuserinfo")
]
