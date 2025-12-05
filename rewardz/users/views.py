from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import redirect, render


def staff_check(user):
    return user.is_authenticated and user.is_staff


staff_required = user_passes_test(staff_check, login_url="/admin/login/")


@login_required(login_url="/admin/login/")
@staff_required
def add_student(request):
    """
    Simple form for superadmin/staff to create a new student user.
    """
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not (username and password):
            error = "Username and password are required."
        elif User.objects.filter(username=username).exists():
            error = "A user with this username already exists."
        else:
            User.objects.create_user(
                username=username,
                email=email or "",
                password=password,
                is_staff=False,
            )
            return redirect("dashboard")

    return render(
        request,
        "add_student.html",
        {
            "error": error,
        },
    )

