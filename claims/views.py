from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models import Sum,Case, When, IntegerField, FloatField
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
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
from .models import Transaction,EDICLHP,Fund_Data,Fund_Status,Total_Charges
from .utils import extract_837_data,parse_df
import re
from datetime import datetime

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
        # for filename in os.listdir(folder_path):
        #     file_path = os.path.join(
        #         folder_path,
        #         filename
        #     )
        #     if os.path.isfile(file_path):
        #         try:
        #             os.remove(file_path)
        #             print(f"Deleted: {file_path}")
        #         except Exception as e:
        #             print(
        #                 f"Failed to delete {file_path}: {e}"
        #             )
        # if process_flag:
        #     process_claims.delay(excel_file,filetype,im_file)    
        return Response(
        {
            "success": True,
            "count": len(response_data),
            "data": response_data
        }
    )