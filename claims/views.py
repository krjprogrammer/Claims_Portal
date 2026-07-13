from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum,Case, When, IntegerField, FloatField
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import pyotp
import random
import qrcode
import base64
import io
from django.db.models.functions import Cast
import os
import sqlite3
import io
from .tasks import process_claims
from rest_framework import status
import requests
from datetime import date
import json
from django.conf import settings
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Transaction,EDICLHP,Fund_Data,Fund_Status,Total_Charges,ProcessingLog, PendingVerification, Member, VerificationHistory, VerificationStatus
from .models import PendingVerification, Member, VerificationHistory, VerificationStatus
from .helpers import calculate_match_candidates, build_comparison_matrix
from .utils import extract_837_data,parse_df
import re
from datetime import datetime
from .models import PortalUser, PortalRoles, PortalPages, EmailOTP
from .ser import (
    PortalUserSerializer, PortalUserShowSerializer, RegisterSaveSerializer,
    PortalRolesSerializer, PortalPagesSerializer, EmailSerializer, OTPVerifySerializer
)
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.core import signing
from .utils import send_mail
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

folder_path = "/home/ubuntu/claim_files/837_Files_today"


class ProcessedFilesCountAPIView(APIView):

    def post(self, request):
        try:
            selected_date = request.data.get("date")

            if not selected_date:
                return Response(
                    {
                        "success": False,
                        "error": "date is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = Transaction.objects.filter(
                created_date=selected_date
            )

            total_files = queryset.values("filename").distinct().count()

            professional_files = queryset.filter(
                filetype="P"
            ).values("filename").distinct().count()

            institutional_files = queryset.filter(
                filetype="I"
            ).values("filename").distinct().count()

            return Response({
                "success": True,
                "date": selected_date,
                "processed_files": total_files,
                "professional_files": professional_files,
                "institutional_files": institutional_files
            })

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClaimsCountAPIView(APIView):

    def post(self, request):

        try:

            selected_date = request.data.get("date")

            if not selected_date:
                return Response(
                    {
                        "success": False,
                        "error": "date is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = Transaction.objects.filter(
                created_date=selected_date
            )

            total_claims = queryset.aggregate(
                total=Sum("claim_count")
            )["total"] or 0

            professional_claims = queryset.filter(
                filetype="P"
            ).aggregate(
                total=Sum("claim_count")
            )["total"] or 0

            institutional_claims = queryset.filter(
                filetype="I"
            ).aggregate(
                total=Sum("claim_count")
            )["total"] or 0

            return Response({
                "success": True,
                "date": selected_date,
                "total_claims": total_claims,
                "professional_claims": professional_claims,
                "institutional_claims": institutional_claims
            })

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ClaimsCountRangeAPIView(APIView):

    def post(self, request):

        try:

            from_date = request.data.get("from_date")
            to_date = request.data.get("to_date")

            range_type = request.data.get("type")

            if not from_date or not to_date:

                return Response(
                    {
                        "success": False,
                        "error": "from_date and to_date are required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = Transaction.objects.filter(
                created_date__gte=from_date,
                created_date__lte=to_date
            )

            total_claims = queryset.aggregate(
                total=Sum("claim_count")
            )["total"] or 0

            professional_claims = queryset.filter(
                filetype="P"
            ).aggregate(
                total=Sum("claim_count")
            )["total"] or 0

            institutional_claims = queryset.filter(
                filetype="I"
            ).aggregate(
                total=Sum("claim_count")
            )["total"] or 0

            return Response(
                {
                    "success": True,
                    "from_date": from_date,
                    "to_date": to_date,
                    "type": range_type,
                    "total_claims": total_claims,
                    "professional_claims": professional_claims,
                    "institutional_claims": institutional_claims
                }
            )

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProcessedFilesAPIView(APIView):

    def post(self, request):

        try:

            selected_date = request.data.get("date")

            if not selected_date:
                return Response(
                    {
                        "success": False,
                        "error": "date is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            filenames = list(
                Transaction.objects.filter(
                    created_date=selected_date
                )
                .values_list("filename", flat=True)
                .distinct()
                .order_by("filename")
            )

            return Response({
                "success": True,
                "date": selected_date,
                "total_files": len(filenames),
                "filenames": filenames
            })

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class FileDataAPIView(APIView):

    def post(self, request):

        try:

            filename = request.data.get("filename")

            if not filename:
                return Response(
                    {
                        "success": False,
                        "error": "filename is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            records = EDICLHP.objects.filter(
                filename=filename
            )

            data = list(
                records.values()
            )

            return Response({
                "success": True,
                "filename": filename,
                "record_count": len(data),
                "data": data
            })

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class FundCountAPIView(APIView):

    def get(self, request):

        data = Fund_Data.objects.all()

        file_name = request.GET.get("file_name", "")
        file_date = request.GET.get("file_date", "")

        if file_name:
            data = data.filter(filename=file_name)

        if file_date:
            data = data.filter(file_date=file_date)

        result = (
            data
            .values("FUND")
            .annotate(
                prof_count=Sum(
                    Case(
                        When(
                            fund_type="P",
                            then=Cast("CLAIMS", IntegerField())
                        ),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
                inst_count=Sum(
                    Case(
                        When(
                            fund_type="I",
                            then=Cast("CLAIMS", IntegerField())
                        ),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            )
            .order_by("FUND")
        )

        return Response({
            "success": True,
            "count": len(result),
            "data": list(result)
        })
    

class FundDashboardAPI(APIView):

    def post(self, request):

        file_date = request.data.get("file_date", "")
        filename = request.data.get("file_name", "")

        if not file_date and not filename:
            return Response(
                {
                    "error": "Provide file_date or filename"
                },
                status=400
            )

        queryset = Fund_Data.objects.all()

        if file_date and filename:
            queryset = queryset.filter(
                file_date=file_date,
                filename=filename
            )

        elif file_date:
            queryset = queryset.filter(
                file_date=file_date
            )

        elif filename:
            queryset = queryset.filter(
                filename=filename
            )

        result = {}

        for row in queryset.values(
            "FUND",
            "CLAIMS",
            "claim_amount",
            "allowed_amount",
            "paid_amount",
            "group_name",
            "group_count",
            "fund_type"
        ):

            fund = row["FUND"]

            if fund not in result:

                result[fund] = {
                    "fund": fund,
                    "count": row["CLAIMS"],
                    "claim_amount": row["claim_amount"],
                    "allowed_amount": row["allowed_amount"],
                    "paid_amount": row["paid_amount"],
                    "fund_type": row["fund_type"],
                    "groups": {}
                }

            result[fund]["groups"][
                row["group_name"]
            ] = row["group_count"]

        return Response(
            {
                "success": True,
                "count": len(result),
                "data": list(result.values())
            }
        )
    

class FundDashboardRangeAPI(APIView):

    def post(self, request):

        from_date = request.data.get("from_date", "")
        to_date = request.data.get("to_date", "")
        range_type = request.data.get("type", "")  # W/M/Q/Y

        if not from_date or not to_date:

            return Response(
                {
                    "success": False,
                    "error": "from_date and to_date are required"
                },
                status=400
            )

        queryset = Fund_Data.objects.filter(
            file_date__gte=from_date,
            file_date__lte=to_date
        )

        result = {}

        seen_totals = set()

        for row in queryset.values(
            "FUND",
            "CLAIMS",
            "claim_amount",
            "allowed_amount",
            "paid_amount",
            "group_name",
            "group_count",
            "fund_type",
            "file_date"
        ):

            fund = row["FUND"]

            if fund not in result:

                result[fund] = {
                    "fund": fund,
                    "count": 0,
                    "claim_amount": 0.0,
                    "allowed_amount": 0.0,
                    "paid_amount": 0.0,
                    "fund_type": row["fund_type"],
                    "groups": {}
                }

            # Count fund totals only once per fund/date/type
            total_key = (
                row["FUND"],
                row["file_date"],
                row["fund_type"]
            )

            if total_key not in seen_totals:

                result[fund]["count"] += int(
                    row["CLAIMS"] or 0
                )

                result[fund]["claim_amount"] += float(
                    row["claim_amount"] or 0
                )

                result[fund]["allowed_amount"] += float(
                    row["allowed_amount"] or 0
                )

                result[fund]["paid_amount"] += float(
                    row["paid_amount"] or 0
                ) if row["paid_amount"] not in [None, "", "NaN"] else 0

                seen_totals.add(total_key)

            # Always aggregate group counts
            group_name = row["group_name"]

            if group_name not in result[fund]["groups"]:

                result[fund]["groups"][group_name] = 0

            result[fund]["groups"][group_name] += int(
                row["group_count"] or 0
            )

        return Response(
            {
                "success": True,
                "from_date": from_date,
                "to_date": to_date,
                "type": range_type,
                "count": len(result),
                "data": list(result.values())
            }
        )

class ActiveFundCountAPIView(APIView):

    def get(self, request):

        active_funds = (
            Fund_Status.objects
            .filter(Status="A")
            .values_list("Fund", flat=True)
            .distinct()
        )

        return Response(
            {
                "success": True,
                "active_fund_count": len(active_funds),
                "active_funds": list(active_funds)
            }
        )
    
class TotalChargesAPIView(APIView):

    def post(self, request):

        selected_date = request.data.get("date")

        if not selected_date:
            return Response(
                {
                    "success": False,
                    "error": "date is required"
                },
                status=400
            )

        queryset = Total_Charges.objects.filter(
            file_date=selected_date
        )

        return Response(
            {
                "success": True,
                "date": selected_date,

                "total_claim_amount":
                    queryset.aggregate(
                        total=Sum(
                            Cast(
                                "total_claim_amount",
                                FloatField()
                            )
                        )
                    )["total"] or 0,

                "total_allowed_amount":
                    queryset.aggregate(
                        total=Sum(
                            Cast(
                                "total_allowed_amount",
                                FloatField()
                            )
                        )
                    )["total"] or 0,

                "total_paid_amount":
                    queryset.aggregate(
                        total=Sum(
                            Cast(
                                "total_paid_amount",
                                FloatField()
                            )
                        )
                    )["total"] or 0,
            }
        )
    

class TotalChargesRangeAPIView(APIView):

    def post(self, request):

        from_date = request.data.get("from_date")
        to_date = request.data.get("to_date")
        range_type = request.data.get("type")

        if not from_date or not to_date:

            return Response(
                {
                    "success": False,
                    "error": "from_date and to_date are required"
                },
                status=400
            )

        queryset = Total_Charges.objects.filter(
            file_date__gte=from_date,
            file_date__lte=to_date
        )

        return Response(
            {
                "success": True,
                "from_date": from_date,
                "to_date": to_date,
                "type": range_type,

                "total_claim_amount":
                    queryset.aggregate(
                        total=Sum(
                            Cast(
                                "total_claim_amount",
                                FloatField()
                            )
                        )
                    )["total"] or 0,

                "total_allowed_amount":
                    queryset.aggregate(
                        total=Sum(
                            Cast(
                                "total_allowed_amount",
                                FloatField()
                            )
                        )
                    )["total"] or 0,

                "total_paid_amount":
                    queryset.aggregate(
                        total=Sum(
                            Cast(
                                "total_paid_amount",
                                FloatField()
                            )
                        )
                    )["total"] or 0,
            }
        )
    
class ClaimDetailsAPIView(APIView):

    def post(self, request):

        try:

            bhdocn = request.data.get("BHDOCN")

            if not bhdocn:

                return Response(
                    {
                        "success": False,
                        "error": "BHDOCN is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            record = EDICLHP.objects.filter(
                BHDOCN=bhdocn
            ).values(
                "BHMEMN",
                "BHCLNT",
                "BHCLTP",
                "BHPNAM",
                "BHTXID",
                "BHPHNM",
                "BHPHID",
                "BHBFRD",
                "BHRECD",
                "BHCHGA"
            ).first()

            if not record:

                return Response(
                    {
                        "success": False,
                        "error": "No record found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "success": True,
                    "data": record
                }
            )

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class FileCountTypeAPIView(APIView):
    def get(self,request):
        response_data = []
        temp_dir = "/home/ubuntu/claim_temp_files"
        process_flag = False
        to_cel_filedate = ''
        to_cel_filename = ''
        os.makedirs(
            temp_dir,
            exist_ok=True
        )
        mappings = [{"field": "BHCHGA", "description": "Claim Charge Amount", "segment": "CLM", "entity": "", "qualifier": "", "element": "CLM02"}, {"field": "BHPLSR", "description": "Place Of Service", "segment": "CLM", "entity": "", "qualifier": "", "element": "CLM05"}, {"field": "BHFREQ", "description": "Claim Frequency Code", "segment": "CLM", "entity": "", "qualifier": "", "element": "CLM05"}, {"field": "BHACPA", "description": "Assignment Indicator", "segment": "CLM", "entity": "", "qualifier": "", "element": "CLM07"}, {"field": "BHDASG", "description": "Benefits Assignment", "segment": "CLM", "entity": "", "qualifier": "", "element": "CLM08"}, {"field": "BHRELI", "description": "Release Of Info", "segment": "CLM", "entity": "", "qualifier": "", "element": "CLM09"}, {"field": "BHDMRE", "description": "Claim Remark Code", "segment": "CLM", "entity": "", "qualifier": "", "element": "CLM01"}, {"field": "BHMFNM", "description": "Subscriber First Name", "segment": "NM1", "entity": "", "qualifier": "IL", "element": "NM104"}, {"field": "BHMLNM", "description": "Subscriber Last Name", "segment": "NM1", "entity": "", "qualifier": "IL", "element": "NM103"}, {"field": "BHMINT", "description": "Subscriber Initials", "segment": "NM1", "entity": "", "qualifier": "IL", "element": "NM105"}, {"field": "BHMID", "description": "Subscriber Member ID", "segment": "REF", "entity": "", "qualifier": "SY", "element": "REF02"}, {"field": "BHMAD1", "description": "Subscriber Address", "segment": "N3", "entity": "Subscriber", "qualifier": "", "element": "N301"}, {"field": "BHMCTY", "description": "Subscriber City", "segment": "N4", "entity": "Subscriber", "qualifier": "", "element": "N401"}, {"field": "BHMST", "description": "Subscriber State", "segment": "N4", "entity": "Subscriber", "qualifier": "", "element": "N402"}, {"field": "BHMZIP", "description": "Subscriber ZIP Code", "segment": "N4", "entity": "Subscriber", "qualifier": "", "element": "N403"}, {"field": "BHMBDT", "description": "Subscriber DOB", "segment": "DMG", "entity": "Subscriber", "qualifier": "", "element": "DMG02"}, {"field": "BHMSEX", "description": "Subscriber SEX", "segment": "DMG", "entity": "Subscriber", "qualifier": "", "element": "DMG03"}, {"field": "BHDFNM", "description": "Dependent Full Name", "segment": "NM1", "entity": "", "qualifier": "QC", "element": "NM104"}, {"field": "BHDLNM", "description": "Dependent Full Name", "segment": "NM1", "entity": "", "qualifier": "QC", "element": "NM103"}, {"field": "BHDINT", "description": "Dependent Initials", "segment": "NM1", "entity": "", "qualifier": "QC", "element": "NM105"}, {"field": "BHDAD1", "description": "Dependent Address", "segment": "N3", "entity": "Dependent", "qualifier": "", "element": "N301"}, {"field": "BHDCTY", "description": "Dependent City", "segment": "N4", "entity": "Dependent", "qualifier": "", "element": "N401"}, {"field": "BHDST", "description": "Dependent State", "segment": "N4", "entity": "Dependent", "qualifier": "", "element": "N402"}, {"field": "BHDZIP", "description": "Dependent ZIP Code", "segment": "N4", "entity": "Dependent", "qualifier": "", "element": "N403"}, {"field": "BHDBDT", "description": "Dependent DOB", "segment": "DMG", "entity": "Dependent", "qualifier": "", "element": "DMG02"}, {"field": "BHDSEX", "description": "Dependent SEX", "segment": "DMG", "entity": "Dependent", "qualifier": "", "element": "DMG03"}, {"field": "BHPNAM", "description": "Billing Provider Name", "segment": "NM1", "entity": "", "qualifier": "85", "element": "NM103"}, {"field": "BHNPI", "description": "Billing Provider NPI", "segment": "NM1", "entity": "", "qualifier": "85", "element": "NM109"},{"field": "BLPAD1", "description": "Billing Address", "segment": "N3", "entity": "Billing", "qualifier": "85", "element": "N301"}, {"field": "BLPCTY", "description": "Billing City", "segment": "N4", "entity": "Billing", "qualifier": "85", "element": "N401"}, {"field": "BLPST", "description": "Billing State", "segment": "N4", "entity": "Billing", "qualifier": "85", "element": "N402"}, {"field": "BLPZIP", "description": "Billing Zip", "segment": "N4", "entity": "Billing", "qualifier": "85", "element": "N403"},{"field": "BHPTEL", "description": "Billing Phone", "segment": "PER", "entity": "", "qualifier": "", "element": "PER04"}, {"field": "BHTXID", "description": "Billing EIN Reference", "segment": "REF", "entity": "", "qualifier": "EI", "element": "REF02"}, {"field": "BHTXSN", "description": "Tax ID SSN Reference", "segment": "REF", "entity": "", "qualifier": "TJ", "element": "REF02"}, {"field": "BHPAD1", "description": "Pay-To Address", "segment": "N3", "entity": "PayTo", "qualifier": "", "element": "N301"}, {"field": "BHPCTY", "description": "Pay-To City", "segment": "N4", "entity": "PayTo", "qualifier": "", "element": "N401"}, {"field": "BHPST", "description": "Pay-To State", "segment": "N4", "entity": "PayTo", "qualifier": "", "element": "N402"}, {"field": "BHPZIP", "description": "Pay-To ZIP Code", "segment": "N4", "entity": "PayTo", "qualifier": "", "element": "N403"}, {"field": "BHPHNM", "description": "Attending Physician Name", "segment": "NM1", "entity": "Attending Physician", "qualifier": "82", "element": "NM103 + NM104"}, {"field": "BHPHID", "description": "Attending Physician NPI", "segment": "NM1", "entity": "Attending Physician", "qualifier": "82", "element": "NM109"}, {"field": "BHSNAM", "description": "Service Location Name", "segment": "NM1", "entity": "", "qualifier": "77", "element": "NM103"}, {"field": "BHSID", "description": "Service Location ID", "segment": "NM1", "entity": "Service Location", "qualifier": "77", "element": "NM109"}, {"field": "BHSAD1", "description": "Service Location Address", "segment": "N3", "entity": "Service Location", "qualifier": "77", "element": "N301"}, {"field": "BHSCTY", "description": "Service Location City", "segment": "N4", "entity": "Service Location", "qualifier": "77", "element": "N401"}, {"field": "BHSST", "description": "Service Location State", "segment": "N4", "entity": "Service Location", "qualifier": "77", "element": "N402"}, {"field": "BHSZIP", "description": "Service Location Zip", "segment": "N4", "entity": "Service Location", "qualifier": "77", "element": "N403"}, {"field": "BHSNPINS", "description": "Institutional ID", "segment": "NM1", "entity": "", "qualifier": "71", "element": "NM109"},{"field": "BHSNPIDN", "description": "Institutional ID", "segment": "NM1", "entity": "", "qualifier": "DN", "element": "NM109"}, {"field": "BHDOCN", "description": "Claim Control Number", "segment": "REF", "entity": "", "qualifier": "F8", "element": "REF02"}, {"field": "BHADJR", "description": "Adjustment Reason Code", "segment": "REF", "entity": "", "qualifier": "9C", "element": "REF02"}, {"field": "BHORGN", "description": "Original Reference Number", "segment": "REF", "entity": "", "qualifier": "SY", "element": "REF02"}, {"field": "BHCFID", "description": "Subscriber Config ID", "segment": "SBR", "entity": "", "qualifier": "", "element": "SBR09"}, {"field": "BHGRPN", "description": "Group Number", "segment": "SBR", "entity": "", "qualifier": "", "element": "SBR03"}, {"field": "BHGRNM", "description": "Group Name", "segment": "SBR", "entity": "", "qualifier": "", "element": "SBR04"}, {"field": "BHPID", "description": "Provider Identifier", "segment": "PRV", "entity": "", "qualifier": "", "element": "PRV03"}, {"field": "BHTAXO", "description": "Taxonomy Code", "segment": "PRV", "entity": "", "qualifier": "PE", "element": "PRV03"},{"field": "BHTAXO2", "description": "Taxonomy Code2", "segment": "PRV", "entity": "", "qualifier": "BI", "element": "PRV03"}, {"field": "BHPRVT", "description": "Provider Code", "segment": "PRV", "entity": "", "qualifier": "", "element": "PRV01"}, {"field": "BHPSTS", "description": "Patient Status Code", "segment": "CL1", "entity": "", "qualifier": "", "element": "CL103"}, {"field": "BHOICO", "description": "OI Copay Amount", "segment": "CAS", "entity": "", "qualifier": "PR", "element": "CAS03"}, {"field": "BHOICP", "description": "OI Copay Percentage", "segment": "CAS", "entity": "", "qualifier": "PR", "element": "CAS03"}, {"field": "BHOIDE", "description": "OI Deductible", "segment": "CAS", "entity": "", "qualifier": "PR", "element": "CAS03"}, {"field": "BHNPA1", "description": "Non-Payable Amount 1", "segment": "CAS", "entity": "", "qualifier": "CO", "element": "CAS03"}, {"field": "BHNPR2", "description": "Non-Payable Reason 2", "segment": "CAS", "entity": "", "qualifier": "CO", "element": "CAS05"}, {"field": "BHNPA2", "description": "Non-Payable Amount 2", "segment": "CAS", "entity": "", "qualifier": "CO", "element": "CAS06"}, {"field": "BHOPPA", "description": "Patient Paid Amount", "segment": "AMT", "entity": "", "qualifier": "D", "element": "AMT02"}, {"field": "BHMEDA", "description": "Medical Amount", "segment": "AMT", "entity": "", "qualifier": "D", "element": "AMT02"}, {"field": "BHCALA", "description": "Calculated Amount", "segment": "AMT", "entity": "", "qualifier": "EAF", "element": "AMT02"}, {"field": "BHCNRF", "description": "Contract Reference", "segment": "CN1", "entity": "", "qualifier": "", "element": "CN105"}, {"field": "BHNOTC", "description": "Note Type Code", "segment": "NTE", "entity": "", "qualifier": "", "element": "NTE01"}, {"field": "BHNOTE", "description": "Note Text", "segment": "NTE", "entity": "", "qualifier": "", "element": "NTE02"}, {"field": "BHDIO1", "description": "Diagnosis Code 1", "segment": "HI", "entity": "", "qualifier": "", "element": "HI01"}, {"field": "BHDIO2", "description": "Diagnosis Code 2", "segment": "HI", "entity": "", "qualifier": "", "element": "HI02"}, {"field": "BHDIO3", "description": "Diagnosis Code 3", "segment": "HI", "entity": "", "qualifier": "", "element": "HI03"}, {"field": "BHDIO4", "description": "Diagnosis Code 4", "segment": "HI", "entity": "", "qualifier": "", "element": "HI04"}, {"field": "BHDIO5", "description": "Diagnosis Code 5", "segment": "HI", "entity": "", "qualifier": "", "element": "HI05"}, {"field": "BHDIO6", "description": "Diagnosis Code 6", "segment": "HI", "entity": "", "qualifier": "", "element": "HI06"}, {"field": "BHDIO7", "description": "Diagnosis Code 7", "segment": "HI", "entity": "", "qualifier": "", "element": "HI07"}, {"field": "BHDIO8", "description": "Diagnosis Code 8", "segment": "HI", "entity": "", "qualifier": "", "element": "HI08"}, {"field": "BHCAMT", "description": "Allowed Amount", "segment": "HCP", "entity": "", "qualifier": "", "element": "HCP02"}, {"field": "BHPAYC", "description": "Pricing Pay Code", "segment": "HCP", "entity": "", "qualifier": "", "element": "HCP06"}, {"field": "BHPPOI", "description": "Pricing Policy Indicator", "segment": "HCP", "entity": "", "qualifier": "", "element": "HCP06"}, {"field": "BHREV", "description": "Revenue Code", "segment": "HCP", "entity": "", "qualifier": "", "element": "HCP01"}, {"field": "BHACDT", "description": "RECEIPT DATE", "segment": "BHT", "entity": "", "qualifier": "", "element": "BHT03"}, {"field": "BHRECD", "description": "Claim Received Date", "segment": "DTP", "entity": "", "qualifier": "050", "element": "DTP03"}, {"field": "BHBFRD", "description": "Service From Date", "segment": "DTP", "entity": "", "qualifier": "472", "element": "DTP03"}, {"field": "BHBTOD", "description": "Service To Date", "segment": "DTP", "entity": "", "qualifier": "472", "element": "DTP03"}, {"field": "BHADMD", "description": "Admission Date", "segment": "DTP", "entity": "", "qualifier": "435", "element": "DTP03"}]
        for filename in os.listdir(folder_path):

            file_path = os.path.join(
                folder_path,
                filename
            )

            if not os.path.isfile(file_path):
                continue

            if filename.startswith("HCP"):

                filetype = "P"

            elif filename.startswith("HCI"):

                filetype = "I"

            else:

                continue

            rows, file_type, filename,file_dt = extract_837_data(
                file_path
            )
            formatted_date = datetime.strptime(
                file_dt,
                "%m%d%Y"
            ).strftime("%Y-%m-%d")
            im_df = pd.DataFrame(rows)
            if filetype == 'P':
                im_file = os.path.join(
                temp_dir,
                f"im.xlsx"
                )
                im_df.to_excel(
                    im_file,
                    index=False
                )
            if filetype == 'I':
                df = im_df
                rows_to_drop = []

                i = 0

                while i < len(df):

                    if df.iloc[i]['BIIDFR'] == 'HI':

                        combined_value = str(df.iloc[i]['BIDAT1']).strip()

                        j = i + 1

                        while j < len(df) and df.iloc[j]['BIIDFR'] == 'HI':

                            current_parts = str(df.iloc[j]['BIDAT1']).strip().split()

                            current_value = "  ".join(current_parts[1:])

                            combined_value += "  " + current_value

                            rows_to_drop.append(df.index[j])

                            j += 1

                        df.at[df.index[i], 'BIDAT1'] = combined_value

                        i = j

                    else:
                        i += 1

                df.drop(rows_to_drop, inplace=True)
                df.reset_index(drop=True, inplace=True)
                im_df = df
            biccbt = str(im_df["BICCBT"].iloc[0])
            date_str = str(datetime.strptime(biccbt[:6], "%y%m%d").strftime("%m/%d/%Y"))
            df = parse_df(im_df,mappings)
            df['BHCCBT'] = date_str
            df['BHRECD'] = date_str
            df['BHCNTN'] = date_str + (df.index + 1).astype(str)
            df['BHSNDI'] = 'ANTHEM-ABC'
            df_new_rows = []
            i = 0
            df_new_rows = []

            while i < len(df):

                row1 = df.iloc[i].copy()

                if i + 1 < len(df):

                    row2 = df.iloc[i + 1]

                    if (
                        pd.notna(row1.get("BHPNAM"))
                        and str(row1.get("BHPNAM")).strip() != ""

                        and

                        (
                            pd.isna(row2.get("BHPNAM"))
                            or str(row2.get("BHPNAM")).strip() == ""
                        )
                    ):

                        for col in df.columns:

                            if pd.isna(row1[col]) or row1[col] == "":
                                row1[col] = row2[col]

                        df_new_rows.append(row1)

                        i += 2

                    else:

                        df_new_rows.append(row1)

                        i += 1

                else:

                    df_new_rows.append(row1)

                    i += 1

            df = pd.DataFrame(df_new_rows).reset_index(drop=True)
            
            if filetype == 'P':
                excel_file = os.path.join(
                temp_dir,
                f"claims.xlsx"
                )
                df.to_excel(
                excel_file,
                index=False
                )
                process_flag = True
                to_cel_filedate = formatted_date
                to_cel_filename = filename
            unique_claims = (
                df["BHDOCN"]
                .astype(str)
                .str.strip()
                .nunique()
            )

            response_data.append(
                {
                    "filename": filename,
                    "filetype": file_type,
                    "claim_count": unique_claims,
                    "file_date": formatted_date
                }
            )

        for row in response_data:
            if Transaction.objects.filter(
                filename=row["filename"]
            ).exists():
                continue

            Transaction.objects.create(
                filename=row["filename"],
                filetype=row["filetype"],
                claim_count=row["claim_count"],
                created_date=row["file_date"]
            )

        if process_flag:
            process_claims.delay(excel_file,filetype,im_file,to_cel_filedate,to_cel_filename)    
        return Response(
        {
            "success": True,
            "count": len(response_data),
            "data": response_data
        }
    )


class ProcessingLogAPIView(APIView):

    def get(self, request):

        filename = request.GET.get("filename")

        if not filename:
            return Response(
                {
                    "success": False,
                    "error": "filename is required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        logs = ProcessingLog.objects.filter(
            filename=filename
        ).order_by("id")

        if not logs.exists():
            return Response(
                {
                    "success": False,
                    "error": "No logs found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = [
            {
                "filename": log.filename,
                "filetype": log.filetype,
                "file_date": log.file_date,
                "status": log.status,
                "created_time": log.created_time.strftime("%H:%M:%S")
            }
            for log in logs
        ]

        return Response(
            {
                "success": True,
                "count": len(data),
                "data": data
            }
        )
    

MSG_ID_REQUIRED = "ID is required"


def _send_2fa_enabled_email(user):
    if not user.email:
        return
    subject = "Two-Factor Authentication Enabled"
    message = (
        f"Dear {user.username},\n\n"
        f"Two-Factor Authentication (2FA) has been successfully enabled on your Claims Portal account.\n\n"
        f"What this means:\n"
        f"  - Every login will now require a one-time code in addition to your password.\n"
        f"  - This adds an extra layer of security to protect your account.\n\n"
        f"If you did not make this change, please contact the administrator immediately and change your password.\n\n"
        f"Best regards,\n"
        f"Claims Portal Team"
    )
    send_mail(subject=subject, message=message, recipients=user.email)


def _send_2fa_disabled_email(user):
    if not user.email:
        return
    subject = "Two-Factor Authentication Disabled"
    message = (
        f"Dear {user.username},\n\n"
        f"Two-Factor Authentication (2FA) has been disabled on your Claims Portal account.\n\n"
        f"Your account is now protected by your password alone.\n\n"
        f"If you did not make this change, your account may be compromised. "
        f"Please contact the administrator immediately and change your password.\n\n"
        f"Best regards,\n"
        f"Claims Portal Team"
    )
    send_mail(subject=subject, message=message, recipients=user.email)
MSG_PERMISSION_DENIED = "Permission denied."


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin


class PortalUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        query = PortalUser.objects.filter(is_superuser=False)
        if pk is not None:
            user = query.filter(id=pk).first() if isinstance(pk, int) else query.filter(username=pk.lower()).first()
            if not user:
                return Response({"message": "Portal User not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"data": PortalUserShowSerializer(user).data}, status=status.HTTP_200_OK)
        if not request.user.is_superadmin:
            return Response({"message": MSG_PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
        users = query.order_by("created_at")
        return Response({"data": PortalUserShowSerializer(users, many=True).data}, status=status.HTTP_200_OK)

    def put(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_superadmin:
            return Response({"message": MSG_PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
        user = PortalUser.objects.filter(id=pk).first()
        if not user:
            return Response({"message": "Portal User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PortalUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            return Response({"message": "Portal User updated successfully", "data": PortalUserShowSerializer(updated_user).data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_superadmin:
            return Response({"message": MSG_PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
        user = PortalUser.objects.filter(id=pk).first()
        if not user:
            return Response({"message": "Portal User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"message": "Portal User deleted successfully"}, status=status.HTTP_200_OK)


def _issue_jwt(request, user):
    login(request, user)
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "User logged in successfully.",
        "refresh_token": str(refresh),
        "access_token": str(refresh.access_token),
        "logged_user": PortalUserShowSerializer(user).data
    }, status=status.HTTP_200_OK)

from django.db.models import Q
class UserLoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"message": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        

        user = PortalUser.objects.filter(
            Q(username=username) | Q(email=username)
        ).first()
        if user and user.check_password(password):
            if not user.status:
                return Response({"message": "Authentication error: You are no longer an active user."}, status=status.HTTP_400_BAD_REQUEST)
            if user.totp_enabled:
                totp_token = signing.dumps({"user_id": user.id}, salt="totp-login")
                return Response({"requires_totp": True, "totp_token": totp_token}, status=status.HTTP_200_OK)
            return _issue_jwt(request, user)
        return Response({"message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class UserRegisterView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, *args, **kwargs):
        roles = PortalRolesSerializer(PortalRoles.objects.all(), many=True)
        return Response({"roles": roles.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = RegisterSaveSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully", "data": PortalUserShowSerializer(user).data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PortalRolesView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            role = PortalRoles.objects.filter(id=pk).first()
            if not role:
                return Response({"message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"data": PortalRolesSerializer(role).data}, status=status.HTTP_200_OK)
        roles = PortalRoles.objects.all()
        return Response({"data": PortalRolesSerializer(roles, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({"message": "Role name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if PortalRoles.objects.filter(name__iexact=name).exists():
            return Response({"message": "Role already exists"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PortalRolesSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response({"message": "Role created successfully", "data": PortalRolesSerializer(role).data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        role = PortalRoles.objects.filter(id=pk).first()
        if not role:
            return Response({"message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        name = request.data.get('name')
        if name is not None:
            name = name.strip()
            if not name:
                return Response({"message": "Role name is required"}, status=status.HTTP_400_BAD_REQUEST)
            if PortalRoles.objects.filter(name__iexact=name).exclude(id=pk).exists():
                return Response({"message": "Role already exists"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PortalRolesSerializer(role, data=request.data, partial=True)
        if serializer.is_valid():
            updated_role = serializer.save()
            return Response({"message": "Role updated successfully", "data": PortalRolesSerializer(updated_role).data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        role = PortalRoles.objects.filter(id=pk).first()
        if not role:
            return Response({"message": "Role not found"}, status=status.HTTP_404_NOT_FOUND)
        if role.name.lower() == 'superadmin':
            return Response({"message": "Cannot delete the superadmin role"}, status=status.HTTP_400_BAD_REQUEST)
        role.delete()
        return Response({"message": "Role deleted successfully"}, status=status.HTTP_200_OK)


class PortalPagesView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            page = PortalPages.objects.filter(id=pk).first()
            if not page:
                return Response({"message": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"data": PortalPagesSerializer(page).data}, status=status.HTTP_200_OK)
        pages = PortalPages.objects.all()
        return Response({"data": PortalPagesSerializer(pages, many=True).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = PortalPagesSerializer(data=request.data)
        if serializer.is_valid():
            page = serializer.save()
            return Response({"message": "Page created successfully", "data": PortalPagesSerializer(page).data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        page = PortalPages.objects.filter(id=pk).first()
        if not page:
            return Response({"message": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PortalPagesSerializer(page, data=request.data, partial=True)
        if serializer.is_valid():
            updated_page = serializer.save()
            return Response({"message": "Page updated successfully", "data": PortalPagesSerializer(updated_page).data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not pk:
            return Response({"message": MSG_ID_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        page = PortalPages.objects.filter(id=pk).first()
        if not page:
            return Response({"message": "Page not found"}, status=status.HTTP_404_NOT_FOUND)
        page.delete()
        return Response({"message": "Page deleted successfully"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old = request.data.get('old_password')
    
    new = request.data.get('new_password')
    confirm = request.data.get('confirm_password')
    if not old or not new or not confirm:
        return Response({"message": "old_password, new_password and confirm_password are required."}, status=status.HTTP_400_BAD_REQUEST)
    old, new, confirm = str(old), str(new), str(confirm)
    print(old,new,confirm)
    if new != confirm:
        return Response({"message": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)
    if not user.check_password(old):
        return Response({"message": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user.password = make_password(new)
        user.save()
        send_mail(
            subject="Password Changed Successfully",
            message=f"Hello {user.username},\n\nYour password has been changed successfully.\n\nIf you did not initiate this change, please contact support immediately.",
            recipients=user.email
        )
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"message": "Unable to update password."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_email(request):
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        if PortalUser.objects.filter(email=email).exists():
            return Response({"message": "Email exists"}, status=status.HTTP_200_OK)
        return Response({"message": "Email does not exist"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def send_otp(request):
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        user = PortalUser.objects.filter(email=email).first()
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
        otp = str(random.randint(100000, 999999))
        print("otp=",otp)
        EmailOTP.objects.update_or_create(user=user, defaults={"otp": otp, "is_verified": False})
        send_mail(subject="Your OTP Code", message=f"Your OTP is {otp}", recipients=email)
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        try:
            user = PortalUser.objects.get(email=email)
            email_otp = EmailOTP.objects.get(user=user)
            if email_otp.otp == otp:
                email_otp.is_verified = True
                email_otp.save()
                return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        except (PortalUser.DoesNotExist, EmailOTP.DoesNotExist):
            return Response({"message": "User or OTP not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def forgot_password(request):
    serializer = EmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data['email']
    user = PortalUser.objects.filter(email=email).first()
    if not user:
        return Response({"message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
    otp_record = EmailOTP.objects.filter(user=user, is_verified=True).first()
    if not otp_record:
        return Response({"message": "OTP verification required before resetting password."}, status=status.HTTP_400_BAD_REQUEST)
    new = request.data.get('new_password')
    confirm = request.data.get('confirm_password')
    if not new or not confirm:
        return Response({"message": "new_password and confirm_password are required."}, status=status.HTTP_400_BAD_REQUEST)
    new, confirm = str(new), str(confirm)
    if new != confirm:
        return Response({"message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user.password = make_password(new)
        user.save()
        otp_record.is_verified = False
        otp_record.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"message": "Unable to update password."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def check_username_availability(request, username):
    if PortalUser.objects.filter(username=username).exists():
        return Response({"message": False}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": True}, status=status.HTTP_200_OK)


class TOTPSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.totp_secret:
            user.totp_secret = pyotp.random_base32()
            user.save(update_fields=["totp_secret"])
        totp = pyotp.TOTP(user.totp_secret)
        qr_uri = totp.provisioning_uri(name=user.username, issuer_name="ClaimsPortal")

        img = qrcode.make(qr_uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            "secret": user.totp_secret,
            "qr_uri": qr_uri,
            "qr_image": f"data:image/png;base64,{qr_base64}",
        }, status=status.HTTP_200_OK)


class TOTPEnableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        totp_code = request.data.get("totp_code")
        if not totp_code:
            return Response({"message": "totp_code is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.totp_secret:
            return Response({"message": "TOTP setup not initiated. Call GET /totp/setup/ first."}, status=status.HTTP_400_BAD_REQUEST)
        if not pyotp.TOTP(user.totp_secret).verify(str(totp_code), valid_window=1):
            return Response({"message": "Invalid TOTP code."}, status=status.HTTP_400_BAD_REQUEST)
        user.totp_enabled = True
        user.save(update_fields=["totp_enabled"])
        _send_2fa_enabled_email(user)
        return Response({"message": "TOTP enabled successfully."}, status=status.HTTP_200_OK)
    


class TOTPDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        totp_code = request.data.get("totp_code")
        if not totp_code:
            return Response({"message": "totp_code is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.totp_enabled or not user.totp_secret:
            return Response({"message": "TOTP is not enabled."}, status=status.HTTP_400_BAD_REQUEST)
        if not pyotp.TOTP(user.totp_secret).verify(str(totp_code), valid_window=1):
            return Response({"message": "Invalid TOTP code."}, status=status.HTTP_400_BAD_REQUEST)
        user.totp_enabled = False
        user.totp_secret = None
        user.save(update_fields=["totp_enabled", "totp_secret"])
        _send_2fa_disabled_email(user)
        return Response({"message": "TOTP disabled successfully."}, status=status.HTTP_200_OK)


class TOTPLoginVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        totp_token = request.data.get("totp_token")
        totp_code = request.data.get("totp_code")
        if not totp_token or not totp_code:
            return Response({"message": "totp_token and totp_code are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = signing.loads(totp_token, salt="totp-login", max_age=300)
        except signing.SignatureExpired:
            return Response({"message": "TOTP session expired. Please log in again."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
            return Response({"message": "Invalid TOTP token."}, status=status.HTTP_400_BAD_REQUEST)
        user = PortalUser.objects.filter(id=payload.get("user_id")).first()
        if not user or not user.totp_secret:
            return Response({"message": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
        if not pyotp.TOTP(user.totp_secret).verify(str(totp_code), valid_window=1):
            return Response({"message": "Invalid TOTP code."}, status=status.HTTP_401_UNAUTHORIZED)
        return _issue_jwt(request, user)
    


def format_datetime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ') if dt else None

def format_date(d):
    return d.strftime('%Y-%m-%d') if d else None


def list_pending_verifications(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    queryset = PendingVerification.objects.all()
    
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
        
    priority_filter = request.GET.get('priority')
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)
        
    claim_id = request.GET.get('claim__claim_id') or request.GET.get('claim_id')
    if claim_id:
        queryset = queryset.filter(claim__claim_id__icontains=claim_id)
        
    member_id = request.GET.get('claim__member_id') or request.GET.get('member_id')
    if member_id:
        queryset = queryset.filter(claim__member_id__icontains=member_id)
        
    provider = request.GET.get('claim__provider') or request.GET.get('provider')
    if provider:
        queryset = queryset.filter(claim__provider__icontains=provider)
        
    dos_from = request.GET.get('claim__dos__gte') or request.GET.get('dos_from')
    if dos_from:
        queryset = queryset.filter(claim__dos__gte=dos_from)
        
    dos_to = request.GET.get('claim__dos__lte') or request.GET.get('dos_to')
    if dos_to:
        queryset = queryset.filter(claim__dos__lte=dos_to)
        
    data = []
    for pv in queryset:
        data.append({
            'id': pv.id,
            'claim_id': pv.claim.claim_id,
            'member_id': pv.claim.member_id,
            'patient_name': pv.claim.patient_name,
            'dos': format_date(pv.claim.dos),
            'provider': pv.claim.provider,
            'failure_reason': pv.failure_reason,
            'priority': pv.priority,
            'status': pv.status
        })
        
    return JsonResponse(data, safe=False, status=200)


def get_verification_details(request, pk):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    pv = get_object_or_404(PendingVerification.objects.select_related('claim', 'matched_member'), id=pk)
    claim = pv.claim
    candidate_id = request.GET.get('candidate_id')
    selected_member = pv.matched_member
    if candidate_id:
        try:
            selected_member = Member.objects.get(id=candidate_id)
        except Member.DoesNotExist:
            pass

    if not selected_member:
        candidates = calculate_match_candidates(claim)
        if candidates:
            best_candidate_id = candidates[0]['id']
            try:
                selected_member = Member.objects.get(id=best_candidate_id)
            except Member.DoesNotExist:
                pass
                
    comparison_matrix = build_comparison_matrix(claim, selected_member)

    mismatch_type = pv.failure_reason.strip()
    if "Name" in mismatch_type:
        claim_val = claim.patient_name
        member_val = selected_member.full_name if selected_member else "N/A"
        failure_warning_msg = f"The patient Name in claim does not match with our records. Claim Name: {claim_val} | Best Match Name: {member_val}"
    elif "DOB" in mismatch_type or "Date of Birth" in mismatch_type:
        claim_val = claim.dob.strftime('%m/%d/%Y') if claim.dob else "N/A"
        member_val = selected_member.dob.strftime('%m/%d/%Y') if selected_member and selected_member.dob else "N/A"
        failure_warning_msg = f"The patient DOB in claim does not match with our records. Claim DOB: {claim_val} | Best Match DOB: {member_val}"
    elif "SSN" in mismatch_type:
        claim_val = f"XXX-XX-{claim.ssn[-4:]}" if claim.ssn and len(claim.ssn) >= 4 else "N/A"
        member_val = f"XXX-XX-{selected_member.ssn[-4:]}" if selected_member and selected_member.ssn and len(selected_member.ssn) >= 4 else "N/A"
        failure_warning_msg = f"The patient SSN in claim does not match with our records. Claim SSN: {claim_val} | Best Match SSN: {member_val}"
    else:
        claim_val = getattr(claim, pv.failure_reason.lower().replace(' mismatch', '').replace(' invalid', ''), "N/A")
        member_val = getattr(selected_member, pv.failure_reason.lower().replace(' mismatch', '').replace(' invalid', ''), "N/A") if selected_member else "N/A"
        failure_warning_msg = f"The patient {pv.failure_reason.replace('Mismatch', '').replace('Invalid', '').strip()} in claim does not match with our records. Claim Value: {claim_val} | Best Match Value: {member_val}"


    response_data = {
        'id': pv.id,
        'status': pv.status,
        'failure_reason': pv.failure_reason,
        'priority': pv.priority,
        'verifier_notes': pv.verifier_notes or "",
        'manual_override_reason': pv.manual_override_reason or "",
        'resolved_at': format_datetime(pv.resolved_at),
        'matched_member': {
            'id': pv.matched_member.id,
            'full_name': pv.matched_member.full_name,
            'member_id': pv.matched_member.member_id
        } if pv.matched_member else None,
        'claim': {
            'claim_id': claim.claim_id,
            'bhdocn': claim.bhdocn,
            'dos': format_date(claim.dos),
            'received_date': format_datetime(claim.received_date),
            'subscriber_name': claim.subscriber_name,
            'member_id': claim.member_id,
            'group_client': claim.group_client,
            'provider': claim.provider,
            'patient_name': claim.patient_name,
            'dob': format_date(claim.dob),
            'gender': claim.gender,
            'relationship': claim.relationship,
            'ssn': f"XXX-XX-{claim.ssn[-4:]}" if claim.ssn and len(claim.ssn) >= 4 else "XXX-XX-XXXX",
            'total_charge': str(claim.total_charge)
        },
        'failure_warning': failure_warning_msg,
        'comparison': comparison_matrix
    }
    
    return JsonResponse(response_data, status=200)



def get_candidates_and_history(request, pk):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    pv = get_object_or_404(PendingVerification.objects.select_related('claim'), id=pk)

    candidates_list = calculate_match_candidates(pv.claim)

    history_logs = pv.history.all()
    history_list = []
    for h in history_logs:
        history_list.append({
            'id': h.id,
            'event_title': h.event_title,
            'event_description': h.event_description,
            'created_at': format_datetime(h.created_at),
            'created_by': h.created_by
        })

    response_data = {
        'candidates': candidates_list,
        'history': history_list
    }
    
    return JsonResponse(response_data, status=200)



@csrf_exempt
def execute_verification_action(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    pv = get_object_or_404(PendingVerification, id=pk)
    
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body payload'}, status=400)
        
    action_type = payload.get('action_type')
    if not action_type:
        return JsonResponse({'error': 'action_type parameter is required'}, status=400)
        
    user_name = request.user.username if request.user.is_authenticated else "System"
    if action_type == 'save_notes':
        notes = payload.get('verifier_notes')
        override = payload.get('manual_override_reason')
        pv.verifier_notes = notes
        pv.manual_override_reason = override
        pv.save()
        
        VerificationHistory.objects.create(
            verification=pv,
            event_title="Notes Saved",
            event_description=f"Verifier notes and/or override reasons updated by {user_name}.",
            created_by=user_name
        )
        return JsonResponse({'status': 'Notes saved successfully'}, status=200)

    elif action_type == 'approve':
        candidate_id = payload.get('candidate_id')
        override_reason = payload.get('override_reason', '')
        
        if not candidate_id:
            return JsonResponse({'error': 'candidate_id parameter is required for approval'}, status=400)
            
        try:
            member = Member.objects.get(id=candidate_id)
        except Member.DoesNotExist:
            return JsonResponse({'error': f'Candidate Member with ID {candidate_id} not found'}, status=404)
            
        pv.matched_member = member
        pv.status = VerificationStatus.APPROVED
        pv.resolved_at = timezone.now()
        if override_reason:
            pv.manual_override_reason = override_reason
        pv.save()
        
        VerificationHistory.objects.create(
            verification=pv,
            event_title="Match Approved",
            event_description=f"Claim manually matched to member: {member.full_name} ({member.member_id}) by {user_name}.",
            created_by=user_name
        )
        return JsonResponse({'status': 'Claim successfully matched and approved'}, status=200)

    elif action_type == 'reject':
        reason = payload.get('reason', 'Claim rejected during manual review.')
        pv.status = VerificationStatus.REJECTED
        pv.resolved_at = timezone.now()
        pv.save()
        
        VerificationHistory.objects.create(
            verification=pv,
            event_title="Claim Rejected",
            event_description=f"Claim manual verification rejected. Reason: {reason}",
            created_by=user_name
        )
        return JsonResponse({'status': 'Claim successfully rejected'}, status=200)

    elif action_type == 'mark_unverified':
        pv.status = VerificationStatus.UNVERIFIED
        pv.save()
        
        VerificationHistory.objects.create(
            verification=pv,
            event_title="Marked Unverified",
            event_description=f"Claim status updated to Unverified by {user_name}.",
            created_by=user_name
        )
        return JsonResponse({'status': 'Claim marked unverified'}, status=200)

    elif action_type == 're_run':
        VerificationHistory.objects.create(
            verification=pv,
            event_title="Auto Match Re-run",
            event_description=f"Initiated automatic match rules re-run task by {user_name}.",
            created_by=user_name
        )
        return JsonResponse({'status': 'Automated matching engine re-run scheduled successfully'}, status=200)
        
    else:
        return JsonResponse({'error': f'Unsupported action_type: {action_type}'}, status=400)
