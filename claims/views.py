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
from rest_framework import status
import requests
from datetime import date
import json
from django.conf import settings
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Transaction,EDICLHP,Fund_Data,Fund_Status,Total_Charges
import re
from datetime import datetime



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