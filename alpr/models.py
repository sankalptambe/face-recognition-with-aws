from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Alpr(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	image = models.ImageField(upload_to='alpr')
    
	def __str__(self):
		return f'{self.user.username} Alpr'

	def save(self):
		super().save()

		img = Image.open(self.image.path)

		if img.height > 500 or img.width > 500:
			output_size = (500,500)
			img.thumbnail(output_size)
			img.save(self.image.path)