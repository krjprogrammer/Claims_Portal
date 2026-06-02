from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
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
from .models import Transaction,EDICLHP,Fund_Data
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
    def get(self,request):

        data = Fund_Data.objects.all()

        file_name = request.GET.get('file_name','')
        file_date = request.GET.get('file_date','')

        if file_name:
            data = data.filter(filename=file_name)

        if file_date:
            data = data.filter(file_date=file_date)

        result = list(
            data.values(
                'fund_name',
                'inst_count',
                'prof_count'
            )
        )

        return Response(result)
    

class FundDashboardAPI(APIView):

    def post(self, request):

        file_date = request.data.get("file_date",'')
        filename = request.data.get("file_name",'')

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

        data = list(
            queryset.values(
                "FUND",
                "CLAIMS",
                "PAID",
            )
        )

        return Response(
            {
                "success": True,
                "count": len(data),
                "data": data
            }
        )