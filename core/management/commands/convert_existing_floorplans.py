from django.core.management.base import BaseCommand

from core.forms import FloorPlanForm
from core.models import FloorPlan


class Command(BaseCommand):
    help = "Convert existing floor plan files to PNG."

    def handle(self, *args, **options):
        converted = 0
        failed = 0
        for floorplan in FloorPlan.objects.filter(converted_file=""):
            try:
                FloorPlanForm()._convert_to_png(floorplan)
                if floorplan.converted_file:
                    converted += 1
                    self.stdout.write(self.style.SUCCESS(f"Converted {floorplan.file_name}"))
                else:
                    failed += 1
                    self.stdout.write(self.style.WARNING(f"No conversion for {floorplan.file_name}"))
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"Failed {floorplan.file_name}: {e}"))
        self.stdout.write(self.style.SUCCESS(f"Done. Converted: {converted}, Failed: {failed}"))
