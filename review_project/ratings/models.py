from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core import signing

from . import encryption

import datetime

class Profile(models.Model):
    userid = models.CharField(primary_key=True,unique=True,max_length=6,default='')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.CharField(max_length=200)
    can_see = models.BooleanField(default=False)
    can_rate = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    current_rating = models.FloatField(default=0.0,validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    cumulated_rating = models.FloatField(default=0.0,validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])

    public_key = models.TextField()     #user public key

    # ImageField¶ While adding profile pictures
    # class ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, **options)

    def __str__(self):
        return self.userid


    def updateMyRating(self, new_rating, session):
        # A control object must be present
        recent_control = (Control.objects.latest('updated_at'))
        recent_session_number = recent_control.session_number

        total_ratings_taken = Rating.objects.all().filter(user2 = self.userid).filter(session_number = recent_session_number).count()
        recent_ratings_taken = Rating.objects.all().filter(user2 = self.userid).filter(session_number = recent_session_number).count()

        total_ratings_taken = max(total_ratings_taken, 1)
        recent_ratings_taken = max(recent_ratings_taken, 1)

        #  if Divide by zero because of no ratings
        self.current_rating = (self.current_rating * (recent_ratings_taken-1) + int(new_rating)) / recent_ratings_taken
        self.cumulated_rating = (self.cumulated_rating * (total_ratings_taken-1) + int(new_rating)) / total_ratings_taken

        self.save()

    def update_can_see(self, session):
        recent_control = (Control.objects.latest('updated_at'))
        recent_session_number = recent_control.session_number
        threshold = recent_control.threshold_persons

        recent_ratings_given = Rating.objects.all().filter(user1 = self.userid).filter(session_number = recent_session_number).count()

        self.can_see = True if recent_ratings_given > threshold else False
        self.save()

    def get_absolute_url(self):
        return ("/user/"+self.userid)

    def get_latest_work(self):
        works = Work.objects.filter(user=self).order_by('-updated_at').values('work')
        trueworks=[]
        
        for work in works:
            data = work.get('work')
            trueworks.append(data)
        works = trueworks

        try:
            latest_work = works[0]
            decrypted_work = signing.loads(latest_work)
            return decrypted_work[0]
        except:
            return None

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance, userid=instance.username)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

class Rating(models.Model):
    # Session number for versioning
    session_number = models.IntegerField(default=0)

    # user1 rating to user2
    user1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='Profile1')
    user2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='Profile2')

    #Fields to be stored encrypted by public key of reviewer
    rating = models.TextField()
    review = models.TextField()

    #Fields to be stored encrypted by public key of reviewee
    rating2 = models.TextField()
    review2 = models.TextField()

    can_edit = models.BooleanField() # Is the rating editable

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (self.user1.userid + " rated " + self.user2.userid)

class Work(models.Model):
    user = models.ForeignKey(Profile,on_delete=models.CASCADE)
    work = models.CharField(max_length=500,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.work

class Control(models.Model):
    # Control fields
    session_number = models.IntegerField(default=0)
    registration_enabled = models.BooleanField(default=True)
    everyone_can_rate = models.BooleanField(default=True)
    everyone_can_edit = models.BooleanField(default=True) # doesn't overwrite
    update_everyone  = models.BooleanField(default=True)

    threshold_persons = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def updateOthers(self):
        userlist = Profile.objects.all()
        for user in  userlist:
            user.can_rate = self.everyone_can_rate
            user.save()
            if self.update_everyone:
                user.updateMyRating()

        ratings = Rating.objects.all().filter(session_number = self.session_number)

        # For current batch of ratings, make them editable or un-editable
        for rating in ratings:
            rating.can_edit = self.everyone_can_edit
            rating.save()

    def __str__(self):
        return (str(self.session_number))
