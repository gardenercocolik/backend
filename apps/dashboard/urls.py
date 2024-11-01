# backend/apps/dashboard/urls.py

from django.urls import path
<<<<<<< HEAD
from .views import ReportListView, RecordListView, ReportCreateView, RecordSubmitView, ReturnCompetitionNameView, GetUserInfoView, UpdateUserInfoView, ReportApproveView, ReportRejectView, RecordApproveView, RecordRejectView, GeneratePDFView
=======
from .views import ReportListView, RecordListView, ReportCreateView, RecordSubmitView, ReturnCompetitionNameView, GetUserInfoView, UpdateUserInfoView, ReportApproveView, ReportRejectView, RecordApproveView, RecordRejectView , RecordGeneratePdfView
>>>>>>> 182739177bae9e502cad0b11681f046c562d06bc



urlpatterns = [
    path('reports/', ReportListView.as_view(), name='report-list'),
    path('records/', RecordListView.as_view(), name='record-list'),
    path('reports/approve/', ReportApproveView.as_view(), name='report-approve'),
    path('reports/reject/', ReportRejectView.as_view(), name='report-reject'),
    path('reports/create/', ReportCreateView.as_view(), name='report-create'),
    path('records/submit/', RecordSubmitView.as_view(), name='record-submit'),
    path('records/generatepdf/', RecordGeneratePdfView.as_view(), name='record-generatepdf'),
    path('records/approve/', RecordApproveView.as_view(), name='record-approve'),
    path('records/reject/', RecordRejectView.as_view(), name='record-reject'),
    path('reports/return-competition-name/', ReturnCompetitionNameView.as_view(), name='return-competition-name'),
    path('userinfo/', GetUserInfoView.as_view(), name = "userinfo"),
    path('userinfo/update/', UpdateUserInfoView.as_view(), name = "updateuserinfo"),
    path('records/GeneratePDF/', GeneratePDFView.as_view(), name='GeneratePDF')
]
