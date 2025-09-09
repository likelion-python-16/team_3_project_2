import csv
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from cafes.models import CafeId, CafeSales, ResidentPopulation


class Command(BaseCommand):
    help = "Import CafeId and CafeSales data from CSV files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cafe-id-file",
            type=str,
            default="CafeId.csv",
            help="Path to CafeId CSV file",
        )
        parser.add_argument(
            "--cafe-sales-file",
            type=str,
            default="CafeSales.csv",
            help="Path to CafeSales CSV file",
        )
        parser.add_argument(
            "--skip-cafe-id", action="store_true", help="Skip importing CafeId data"
        )
        parser.add_argument(
            "--skip-cafe-sales",
            action="store_true",
            help="Skip importing CafeSales data",
        )

    def handle(self, *args, **options):
        cafe_id_file = options["cafe_id_file"]
        cafe_sales_file = options["cafe_sales_file"]

        if not options["skip_cafe_id"]:
            self.import_cafe_id(cafe_id_file)

        if not options["skip_cafe_sales"]:
            self.import_cafe_sales(cafe_sales_file)

    def import_cafe_id(self, file_path):
        self.stdout.write(f"Importing CafeId data from {file_path}...")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        default_rp, created = ResidentPopulation.objects.get_or_create(
            rp_key=1,
            defaults={
                "total_population": 0,
                "population_per_ages": 0,
                "income_avg": 0,
                "rent_avg": 0,
                "traffic_level": "Unknown",
            },
        )

        success_count = 0
        error_count = 0

        encodings_to_try = ["utf-8-sig", "cp949", "euc-kr", "utf-8"]

        for encoding in encodings_to_try:
            try:
                with open(file_path, "r", encoding=encoding) as test_file:
                    test_file.readline()
                break
            except UnicodeDecodeError:
                continue
        else:
            self.stdout.write(self.style.ERROR("Could not determine file encoding"))
            return

        try:
            with open(file_path, "r", encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile)

                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            cafe_id = CafeId(
                                name=row["name"].strip()
                                if row["name"]
                                else f"Cafe_{row_num}",
                                city=row.get("city", "서울특별시").strip(),
                                distinct=row["distinct"].strip()
                                if row["distinct"]
                                else "",
                                detail_address=row.get("detail_address", "").strip(),
                                franchise=row.get("franchise", "FALSE").upper()
                                == "TRUE",
                                franchise_type=row.get("franchise_type", "").strip(),
                                biz_code=row.get("biz_code", "").strip(),
                                latitude=float(
                                    row.get(
                                        "latitude",
                                        row.get("위도", row.get("����", "0.0")),
                                    )
                                ),
                                longitude=float(
                                    row.get(
                                        "longitude",
                                        row.get("경도", row.get("�浵", "0.0")),
                                    )
                                ),
                                rp_key=default_rp,
                            )
                            cafe_id.full_clean()
                            cafe_id.save()
                            success_count += 1

                            if success_count % 100 == 0:
                                self.stdout.write(
                                    f"Processed {success_count} CafeId records..."
                                )

                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.WARNING(f"Error at row {row_num}: {str(e)}")
                            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading file: {str(e)}"))
            return

        self.stdout.write(
                    self.style.SUCCESS(
                        f"CafeId import completed: {success_count} success, "
                        f"{error_count} errors"
                    )
                )

    def import_cafe_sales(self, file_path):
        self.stdout.write(f"Importing CafeSales data from {file_path}...")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        success_count = 0
        error_count = 0

        try:
            with open(file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            cafe_id = int(row["cafe_id"])

                            try:
                                cafe = CafeId.objects.get(cafe_id=cafe_id)
                            except CafeId.DoesNotExist:
                                error_count += 1
                                self.stdout.write(
                                self.style.WARNING(
                                    f"Row {row_num}: Cafe with ID {cafe_id} not found"
                                )
                            )
                                continue

                            date_str = row["date"].strip()
                            sales = int(float(row["sales"]))
                            visitor_count = int(float(row["visitor_count"]))

                            avg_price = (
                                int(sales / visitor_count) if visitor_count > 0 else 0
                            )

                            cafe_sales, created = CafeSales.objects.get_or_create(
                                cafe=cafe,
                                date=date_str,
                                defaults={
                                    "price": avg_price,
                                    "visitor_count": visitor_count,
                                    "sales": sales,
                                },
                            )

                            if not created:
                                cafe_sales.price = avg_price
                                cafe_sales.visitor_count = visitor_count
                                cafe_sales.sales = sales
                                cafe_sales.save()

                            success_count += 1

                            if success_count % 100 == 0:
                                self.stdout.write(
                                    f"Processed {success_count} CafeSales records..."
                                )

                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.WARNING(f"Error at row {row_num}: {str(e)}")
                            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading file: {str(e)}"))
            return

        self.stdout.write(
                    self.style.SUCCESS(
                        f"CafeSales import completed: {success_count} success, "
                        f"{error_count} errors"
                    )
                )
