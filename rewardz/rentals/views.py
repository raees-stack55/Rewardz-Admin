from datetime import date, timedelta

import requests
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from books.models import Book
from .models import Rental

def fetch_book_data(title: str):
    try:
        clean_title = urllib.parse.quote(title.strip())
        search_url = f"https://openlibrary.org/search.json?title={clean_title}"

        headers = {
            "User-Agent": "RewardzAdminPanel/1.0 (contact: aditya@gmail.com)"
        }

        res = requests.get(search_url, headers=headers, timeout=7)
        res.raise_for_status()
        data = res.json()

        docs = data.get("docs", [])
        if not docs:
            return 100, "Unknown"

        doc = docs[0]

        author_list = doc.get("author_name") or ["Unknown"]
        author = author_list[0]

        edition_keys = doc.get("edition_key", [])
        if not edition_keys:
            return 100, author

        edition_id = edition_keys[0]
        edition_url = f"https://openlibrary.org/books/{edition_id}.json"

        edition_res = requests.get(edition_url, headers=headers, timeout=7)
        edition_res.raise_for_status()
        edition_data = edition_res.json()

        pages = edition_data.get("number_of_pages")

        if pages:
            return int(pages), author

        return 100, author

    except Exception as e:
        print("OpenLibrary API Error:", e)
        return 100, "Unknown"


# def fetch_book_data(title: str):
#     try:
#         clean_title = urllib.parse.quote(title.strip())
#         headers = {
#             "User-Agent": "RewardzAdminPanel/1.0 (contact: aditya@gmail.com)"
#         }

#         # -------- OPENLIBRARY SEARCH --------
#         search_url = f"https://openlibrary.org/search.json?title={clean_title}"
#         res = requests.get(search_url, headers=headers, timeout=10)
#         res.raise_for_status()
#         data = res.json()

#         docs = data.get("docs", [])
#         if docs:
#             doc = docs[0]
#             author_list = doc.get("author_name") or ["Unknown"]
#             author = author_list[0]

#             edition_keys = doc.get("edition_key", [])
#             for edition_id in edition_keys[:5]:
#                 try:
#                     edition_url = f"https://openlibrary.org/books/{edition_id}.json"
#                     edition_res = requests.get(edition_url, headers=headers, timeout=10)
#                     edition_data = edition_res.json()

#                     pages = edition_data.get("number_of_pages")
#                     if pages:
#                         return int(pages), author
#                 except:
#                     pass
#         else:
#             author = "Unknown"

#         # -------- GOOGLE BOOKS FALLBACK --------
#         google_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{clean_title}"
#         g_res = requests.get(google_url, timeout=10)
#         g_data = g_res.json()

#         items = g_data.get("items", [])
#         if items:
#             volume = items[0]["volumeInfo"]
#             author = volume.get("authors", ["Unknown"])[0]
#             pages = volume.get("pageCount", 100)
#             return int(pages), author

#         return 100, author

#     except Exception as e:
#         print("Book API Error:", e)
#         return 100, "Unknown"


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