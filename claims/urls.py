from django.urls import path
from .views import ProcessedFilesAPIView,ProcessedFilesCountAPIView,ClaimsCountAPIView,FileDataAPIView,FundCountAPIView,FundDashboardAPI,ActiveFundCountAPIView,ClaimsCountRangeAPIView,TotalChargesAPIView,TotalChargesRangeAPIView,ClaimDetailsAPIView,FundDashboardRangeAPI,FileCountTypeAPIView,ProcessingLogAPIView
from .views import PortalUserView, UserLoginView, UserLogoutView, UserRegisterView,PortalRolesView, PortalPagesView,change_password, verify_email, send_otp, verify_otp, forgot_password, check_username_availability,TOTPSetupView, TOTPEnableView, TOTPDisableView, TOTPLoginVerifyView
urlpatterns = [
    path('get_file_count',ProcessedFilesCountAPIView.as_view()),
    path('get_claims_count',ClaimsCountAPIView.as_view()),
    path('get_processed_files',ProcessedFilesAPIView.as_view()),
    path('get_file_data',FileDataAPIView.as_view()),
    path('get_fund_count',FundCountAPIView.as_view()),
    path('get_fund_data',FundDashboardAPI.as_view()),
    path('get_fund_data_range',FundDashboardRangeAPI.as_view()),
    path('get_active_funds',ActiveFundCountAPIView.as_view()),
    path('get_claim_count_range',ClaimsCountRangeAPIView.as_view()),
    path('get_charges',TotalChargesAPIView.as_view()),
    path('get_charges_range',TotalChargesRangeAPIView.as_view()),
    path("claim_details",ClaimDetailsAPIView.as_view()),
    path('get_filetype_count',FileCountTypeAPIView.as_view()),
    path('get_logs',ProcessingLogAPIView.as_view()),
    # Users
    path('users/', PortalUserView.as_view(), name='portaluser-list'),
    path('users/<int:pk>/', PortalUserView.as_view(), name='portaluser-detail'),
    path('get-by-username/<str:pk>/', PortalUserView.as_view(), name='portaluser-detail-by-username'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('change-password/', change_password, name='change-password'),
    path('verify-email/', verify_email, name='verify-email'),
    path('send-otp/', send_otp, name='send-otp'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('check-username-availability/<str:username>/', check_username_availability, name='check-username-availability'),
    # TOTP
    path('totp/setup/', TOTPSetupView.as_view(), name='totp-setup'),
    path('totp/enable/', TOTPEnableView.as_view(), name='totp-enable'),
    path('totp/disable/', TOTPDisableView.as_view(), name='totp-disable'),
    path('totp/login-verify/', TOTPLoginVerifyView.as_view(), name='totp-login-verify'),
    # Roles (superadmin only)
    path('roles/', PortalRolesView.as_view(), name='roles-list'),
    path('roles/<int:pk>/', PortalRolesView.as_view(), name='roles-detail'),
    # Pages (superadmin only)
    path('pages/', PortalPagesView.as_view(), name='pages-list'),
    path('pages/<int:pk>/', PortalPagesView.as_view(), name='pages-detail'),
]


