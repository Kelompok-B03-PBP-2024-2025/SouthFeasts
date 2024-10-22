import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.http import HttpResponse
from .models import Makanan
from django.shortcuts import render

def show_main(request):
    context = {}
    return render(request, "main.html", context)

def initialize_makanan_data(request):
    csv_file_path = os.path.join(settings.BASE_DIR, 'dataset/dataset_makanan.csv')

    # with open(csv_file_path, 'r') as file:
    #     csv_reader = csv.DictReader(file)

    #     with transaction.atomic():
    #         Makanan.objects.all().delete()  # Menghapus data yang ada sebelumnya

    #         for row in csv_reader:
    #             Makanan.objects.create(
    #                 item=row['Item'],
    #                 image=row['Image'],
    #                 description=row['Description'],
    #                 categories=row['Categories'],
    #                 price=int(row['Price']),
    #                 resto_name=row['Resto Name'],
    #                 kecamatan=row['Kecamatan'],
    #                 location=row['Location']
    #             )

    # return HttpResponse("Data makanan berhasil diinisialisasi.")