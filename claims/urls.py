from django.urls import path
from .views import ProcessedFilesAPIView,ProcessedFilesCountAPIView,ClaimsCountAPIView,FileDataAPIView,FundCountAPIView,FundDashboardAPI
urlpatterns = [
    path('get_file_count',ProcessedFilesCountAPIView.as_view()),
    path('get_claims_count',ClaimsCountAPIView.as_view()),
    path('get_processed_files',ProcessedFilesAPIView.as_view()),
    path('get_file_data',FileDataAPIView.as_view()),
    path('get_fund_count',FundCountAPIView.as_view()),
    path('get_fund_data',FundCountAPIView.as_view())
]


