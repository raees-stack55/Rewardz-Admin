from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

class Rental(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey("books.Book", on_delete=models.CASCADE)

    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()

    months_rented = models.IntegerField(default=1)

    # ✅ Use Decimal for money (IMPORTANT)
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    total_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    def calculate_fee(self):
        """
        First month is free.
        Fee applies only from 2nd month onward.
        """
        if self.months_rented <= 1:
            self.monthly_fee = Decimal("0.00")
            self.total_fee = Decimal("0.00")
        else:
            self.monthly_fee = Decimal(self.book.pages) / Decimal("100")
            self.total_fee = self.monthly_fee * Decimal(self.months_rented - 1)

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
