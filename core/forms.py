import base64
import os
import tempfile

import fitz
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from PIL import Image
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

from core.models import FloorPlan, Profile, Project

ALLOWED_EXTENSIONS = {".pdf", ".png", ".svg"}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["first_name", "last_name", "role"]


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["project_name", "project_code", "client_name", "project_address", "status"]


class FloorPlanForm(forms.ModelForm):
    file_name = forms.CharField(required=False, max_length=255, label="File name")
    status = forms.ChoiceField(choices=FloorPlan.STATUS_CHOICES, initial="draft", label="Status")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Notes")

    class Meta:
        model = FloorPlan
        fields = ["file", "file_name", "status", "notes"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"accept": ".pdf,.png,.svg"}),
        }

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise ValidationError(f"Only PDF, PNG and SVG files are allowed. Got '{ext}'.")
        return f

    def save(self, project, commit=True):
        instance = super().save(commit=False)
        instance.project = project
        instance.file_name = self.cleaned_data["file_name"] or self.cleaned_data["file"].name
        latest = project.floor_plans.order_by("-version_no").first()
        instance.version_no = (latest.version_no + 1) if latest else 1
        notes = self.cleaned_data["notes"]
        if notes:
            instance.annotate = {"notes": notes}
        if commit:
            instance.save()
            self._convert_to_png(instance)
        return instance

    def _convert_to_png(self, instance):
        original_path = instance.file.path
        ext = os.path.splitext(original_path)[1].lower()
        base_name = os.path.splitext(instance.file_name)[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, f"{base_name}.png")

            try:
                if ext == ".pdf":
                    self._convert_pdf(original_path, png_path)
                elif ext == ".svg":
                    self._convert_svg(original_path, png_path)
                elif ext == ".png":
                    self._convert_image(original_path, png_path)
                else:
                    return

                with open(png_path, "rb") as f:
                    png_name = f"{base_name}.png"
                    instance.converted_file.save(png_name, File(f), save=True)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Failed to convert %s to PNG: %s", instance.file_name, e)

    def _convert_pdf(self, path, output_path):
        doc = fitz.open(path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        pix.save(output_path)
        doc.close()

    def _convert_svg(self, path, output_path):
        drawing = svg2rlg(path)
        if drawing is None:
            raise ValueError(f"Could not parse SVG: {path}")
        renderPM.drawToFile(drawing, output_path, fmt="PNG", dpi=150)

    def _convert_image(self, path, output_path):
        with Image.open(path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(output_path, format="PNG")

    @staticmethod
    def save_cropped(instance, data_url):
        """Overwrite converted_file with a base64 data URL and upload PNG to Supabase Storage."""
        import logging
        logger = logging.getLogger(__name__)

        header, encoded = data_url.split(",", 1)
        img_data = base64.b64decode(encoded)
        base_name = os.path.splitext(instance.file_name)[0]
        png_name = f"{base_name}_cropped.png"

        instance.converted_file.save(png_name, ContentFile(img_data), save=True)

        try:
            from core.supabase_storage import upload_png
            bucket_path = f"floor_plans/{instance.project_id}/{instance.id}/{png_name}"
            public_url = upload_png(bucket_path, img_data)
            instance.supabase_url = public_url
            instance.save(update_fields=["supabase_url"])
            logger.info("Uploaded %s to Supabase: %s", png_name, public_url)
        except Exception as e:
            logger.warning("Supabase upload skipped: %s", e)
