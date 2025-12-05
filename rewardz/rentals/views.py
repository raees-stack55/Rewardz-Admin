from datetime import date, timedelta

import requests
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from books.models import Book
from .models import Rental
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import requests
import urllib.parse


def fetch_book_data(title: str):
    """
    Fetch author name and number of pages for a book from OpenLibrary.
    Returns:
        pages (int), author (str)
    Fallbacks:
        pages = 100
        author = "Unknown"
    """
    try:
        clean_title = urllib.parse.quote(title.strip())
        search_url = f"https://openlibrary.org/search.json?title={clean_title}"
        headers = {
            "User-Agent": "RewardzAdminPanel/1.0 (contact: aditya@gmail.com)"
        }

        response = requests.get(search_url, headers=headers, timeout=7)
        response.raise_for_status()
        data = response.json()
        docs = data.get("docs", [])

        if not docs:
            # Book not found
            return 100, "Unknown"

        doc = docs[0]

        author_list = doc.get("author_name") or ["Unknown"]
        author = author_list[0]

        work_key = doc.get("key")
        if not work_key:
            return 100, author

        editions_url = f"https://openlibrary.org{work_key}/editions.json?limit=10"
        editions_res = requests.get(editions_url, headers=headers, timeout=7)
        editions_res.raise_for_status()
        editions_data = editions_res.json()
        editions = editions_data.get("entries", [])

        for edition in editions:
            pages = edition.get("number_of_pages")
            if pages:
                return int(pages), author

        return 100, author

    except Exception as e:
        print("OpenLibrary API Error:", e)
        return 100, "Unknown"



def staff_check(user):
    return user.is_authenticated and user.is_staff


staff_required = user_passes_test(staff_check, login_url="/admin/login/")


@login_required(login_url="/admin/login/")
@staff_required
def dashboard(request):
    total_students = User.objects.count()
    total_rentals = Rental.objects.count()
    today = date.today()
    active_rentals = Rental.objects.filter(end_date__gte=today).count()
    total_revenue = Rental.objects.aggregate(total=Sum("total_fee"))["total"] or 0
    first_student = User.objects.first()

    context = {
        "total_students": total_students,
        "total_rentals": total_rentals,
        "active_rentals": active_rentals,
        "total_revenue": total_revenue,
        "first_student": first_student,
    }
    return render(request, "dashboard.html", context)


@login_required(login_url="/admin/login/")
@staff_required
def add_rental(request):
    users = User.objects.all()

    if request.method == "POST":
        user_id = request.POST.get("student")
        title = request.POST.get("title")
        end_date_str = request.POST.get("end_date")

        if not (user_id and title and end_date_str):
            return render(
                request,
                "add_rental.html",
                {"users": users, "error": "All fields are required."},
            )

        try:
            year, month, day = map(int, end_date_str.split("-"))
            end_date = date(year, month, day)
        except ValueError:
            return render(
                request,
                "add_rental.html",
                {"users": users, "error": "Invalid end date format."},
            )

        user = get_object_or_404(User, pk=user_id)

        pages, author = fetch_book_data(title)

        book, created = Book.objects.get_or_create(
            title=title.strip(),
            defaults={"author": author, "pages": pages},
        )

        if not created and book.pages == 100:
            book.pages = pages
            book.author = author
            book.save()

        with transaction.atomic():
            Rental.objects.create(
                user=user,
                book=book,
                end_date=end_date,
                months_rented=1,
                monthly_fee=Decimal("0"),
                total_fee=Decimal("0"),
            )

        messages.success(request, "Rental created successfully.")
        return redirect("dashboard")

    initial_end_date = date.today() + timedelta(days=30)

    return render(
        request,
        "add_rental.html",
        {
            "users": users,
            "initial_end_date": initial_end_date.isoformat(),
        },
    )


@login_required(login_url="/admin/login/")
@staff_required
def extend_rental(request):
    rentals = Rental.objects.select_related("book", "user")

    if request.method == "POST":
        rental_id = request.POST.get("rental")
        extra_months_str = request.POST.get("extra_months")

        try:
            extra_months = int(extra_months_str)
            if extra_months <= 0:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Please enter a valid number of extra months.")
            return render(request, "extend_rental.html", {"rentals": rentals})

        if not rental_id:
            messages.error(request, "Please select a rental to extend.")
            return render(request, "extend_rental.html", {"rentals": rentals})

        rental = get_object_or_404(Rental, pk=rental_id)
        pages = rental.book.pages or 100

        monthly_fee = Decimal(pages) / Decimal("100")

        with transaction.atomic():
            rental.months_rented += extra_months
            rental.monthly_fee = monthly_fee
            rental.total_fee = rental.monthly_fee * Decimal(rental.months_rented - 1)
            rental.end_date = rental.end_date + timedelta(days=30 * extra_months)
            rental.save()

        messages.success(
            request,
            f"Rental extended successfully by {extra_months} month(s)."
        )

        return redirect("dashboard")

    return render(request, "extend_rental.html", {"rentals": rentals})


@login_required(login_url="/admin/login/")
@staff_required
def student_dashboard(request, student_id: int):
    students = User.objects.all()
    selected_student = get_object_or_404(User, pk=student_id)
    rentals = (
        Rental.objects.select_related("book")
        .filter(user=selected_student)
        .order_by("-start_date")
    )

    return render(
        request,
        "student_dashboard.html",
        {
            "students": students,
            "selected_student": selected_student,
            "rentals": rentals,
        },
    )