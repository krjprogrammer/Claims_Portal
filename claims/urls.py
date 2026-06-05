from django.urls import path
from .views import ProcessedFilesAPIView,ProcessedFilesCountAPIView,ClaimsCountAPIView,FileDataAPIView,FundCountAPIView,FundDashboardAPI,ActiveFundCountAPIView,ClaimsCountRangeAPIView,TotalChargesAPIView,TotalChargesRangeAPIView,ClaimDetailsAPIView
urlpatterns = [
    path('get_file_count',ProcessedFilesCountAPIView.as_view()),
    path('get_claims_count',ClaimsCountAPIView.as_view()),
    path('get_processed_files',ProcessedFilesAPIView.as_view()),
    path('get_file_data',FileDataAPIView.as_view()),
    path('get_fund_count',FundCountAPIView.as_view()),
    path('get_fund_data',FundDashboardAPI.as_view()),
    path('get_active_funds',ActiveFundCountAPIView.as_view()),
    path('get_claim_count_range',ClaimsCountRangeAPIView.as_view()),
    path('get_charges',TotalChargesAPIView.as_view()),
    path('get_charges_range',TotalChargesRangeAPIView.as_view()),
    path("claim_details",ClaimDetailsAPIView.as_view()),
]


