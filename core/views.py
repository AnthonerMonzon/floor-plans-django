import json

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.forms import FloorPlanForm, ProfileForm, ProjectForm, UserForm
from core.models import FloorPlan, Profile, Project


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user = None
        if user is not None:
            user = authenticate(request, username=user.username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("dashboard")
        error = "Invalid email or password."
    return render(request, "core/login.html", {"error": error})


def logout_view(request):
    auth_logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    return render(request, "core/dashboard.html", {
        "project_count": Project.objects.count(),
        "floorplan_count": FloorPlan.objects.count(),
        "user_count": User.objects.count(),
    })


@login_required
def project_list_view(request):
    projects = Project.objects.all()
    paginator = Paginator(projects, 20)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)
    return render(request, "core/project_list.html", {"page_obj": page_obj})


@login_required
def project_create_view(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            return redirect("project_detail", project_id=project.id)
    else:
        form = ProjectForm()
    return render(request, "core/project_form.html", {"form": form, "title": "New Project"})


@login_required
def project_edit_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("project_detail", project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    return render(request, "core/project_form.html", {"form": form, "title": "Edit Project", "project": project})


@login_required
def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    floor_plans = project.floor_plans.all()
    tab = request.GET.get("tab", "overview")
    return render(request, "core/project_detail.html", {
        "project": project,
        "floor_plans": floor_plans,
        "tab": tab,
    })


@login_required
def floorplan_upload_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == "POST":
        form = FloorPlanForm(request.POST, request.FILES)
        if form.is_valid():
            floorplan = form.save(project=project)
            return redirect("floorplan_editor", project_id=project.id, floorplan_id=floorplan.id)
    else:
        form = FloorPlanForm()
    return render(request, "core/floorplan_form.html", {"form": form, "project": project})


@login_required
def floorplan_editor_view(request, project_id, floorplan_id):
    project = get_object_or_404(Project, id=project_id)
    floorplan = get_object_or_404(FloorPlan, id=floorplan_id, project=project)
    return render(request, "core/floorplan_editor.html", {"project": project, "floorplan": floorplan})


@login_required
@require_POST
def floorplan_save_crop_view(request, project_id, floorplan_id):
    project = get_object_or_404(Project, id=project_id)
    floorplan = get_object_or_404(FloorPlan, id=floorplan_id, project=project)
    try:
        body = json.loads(request.body)
        data_url = body.get("image", "")
        save_as = body.get("save_as", False)
        new_name = body.get("file_name", "").strip()
        if not data_url.startswith("data:image/"):
            return JsonResponse({"error": "Invalid image data."}, status=400)

        if save_as:
            latest = project.floor_plans.order_by("-version_no").first()
            new_version = (latest.version_no + 1) if latest else 1
            new_fp = FloorPlan.objects.create(
                project=project,
                file_name=new_name or f"{floorplan.file_name} (v{new_version})",
                version_no=new_version,
                status=floorplan.status,
                annotate=floorplan.annotate,
                file=floorplan.file,
            )
            FloorPlanForm.save_cropped(new_fp, data_url)
            from django.urls import reverse
            editor_url = reverse("floorplan_editor", kwargs={"project_id": project.id, "floorplan_id": new_fp.id})
            return JsonResponse({
                "ok": True,
                "url": new_fp.converted_file.url,
                "supabase_url": new_fp.supabase_url or None,
                "redirect": editor_url,
                "version": new_fp.version_no,
                "file_name": new_fp.file_name,
            })
        else:
            FloorPlanForm.save_cropped(floorplan, data_url)
            return JsonResponse({
                "ok": True,
                "url": floorplan.converted_file.url,
                "supabase_url": floorplan.supabase_url or None,
            })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def floorplan_viewer_view(request, project_id, floorplan_id):
    project = get_object_or_404(Project, id=project_id)
    floorplan = get_object_or_404(FloorPlan, id=floorplan_id, project=project)
    return render(request, "core/floorplan_viewer.html", {"project": project, "floorplan": floorplan})


@login_required
@require_POST
def floorplan_delete_view(request, project_id, floorplan_id):
    project = get_object_or_404(Project, id=project_id)
    floorplan = get_object_or_404(FloorPlan, id=floorplan_id, project=project)
    floorplan.delete()
    return redirect("project_detail", project_id=project.id)


@login_required
def floorplan_annotate_view(request, project_id, floorplan_id):
    project = get_object_or_404(Project, id=project_id)
    floorplan = get_object_or_404(FloorPlan, id=floorplan_id, project=project)
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            shapes = body.get("shapes", [])
            existing = floorplan.annotate or {}
            existing["shapes"] = shapes
            floorplan.annotate = existing
            floorplan.save(update_fields=["annotate", "updated_at"])
            return JsonResponse({"ok": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return render(request, "core/floorplan_annotate.html", {
        "project": project,
        "floorplan": floorplan,
    })


@login_required
def user_list_view(request):
    users = User.objects.select_related("profile").all()
    paginator = Paginator(users, 20)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)
    return render(request, "core/user_list.html", {"page_obj": page_obj})


@login_required
def user_create_view(request):
    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password("changeme")
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            return redirect("user_list")
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    return render(request, "core/user_form.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "title": "New User",
    })


@login_required
def user_edit_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("user_list")
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    return render(request, "core/user_form.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "title": "Edit User",
        "edit_user": user,
    })
