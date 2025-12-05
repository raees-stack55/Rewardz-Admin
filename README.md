# Rewardz Admin — Library Rental Management System

Rewardz Admin is a Django-based web application designed to manage book rentals efficiently. It allows admins to manage students, track book rentals, extend rental periods, and fetch book data from external APIs.  

This project uses **OpenLibrary API** for book data, with **Google Books** as a fallback.

---

##  Project Setup

Clone the repository to your local machine:

```bash
git clone https://github.com/<your_username>/rewardz-admin.git
cd rewardz-admin


## Environment Setup


# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt


##  API Usage

This project uses external APIs to fetch book information:

OpenLibrary API – Primary source for book details (title, author, pages).

Google Books API – Fallback if OpenLibrary fails.

All API requests are handled in the backend to automatically populate book data when adding or extending rentals.

## Admin Credentials (Demo)

Use the following credentials to log in to the admin panel:

Username: admin

Password: admin123

Superuser: True

You can also create a new superuser using Django’s createsuperuser command.


##  How to Run the Server

Run the following commands in your project directory:

# Apply database migrations
python manage.py migrate

# Create a superuser (if needed)
python manage.py createsuperuser

# Start the development server
python manage.py runserver


Visit http://127.0.0.1:8000/ in your browser to access the app.


## Features

Add, manage, and delete students.

Create new book rentals and track existing ones.

Extend rental periods and calculate fees automatically.

Fetch book details automatically from APIs.

Clean, modern admin dashboard interface.

⚡ Project Structure
rewardz-admin/
│
├── rewardz/            # Django project folder
├── venv/               # Python virtual environment (ignored in Git)
├── manage.py           # Django management script
├── requirements.txt    # Project dependencies
├── README.md           # Project documentation
└── .gitignore          # Git ignore file
