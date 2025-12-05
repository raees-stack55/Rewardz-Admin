from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150, null=True, blank=True)
    pages = models.IntegerField()

    def __str__(self):
        return self.title