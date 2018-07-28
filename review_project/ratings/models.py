from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core import signing
import datetime

def decrypt(encryptedqueryset,string='work'):
    dictionary=encryptedqueryset.values(string)
    trueworks=[]
    for i in dictionary:
        m=i.get(string)
        trueworks.append(m)
    decryptworks=[]
    for i in trueworks:
        n=signing.loads(i)
        decryptworks.append(n[0])
    return decryptworks

class Profile(models.Model):
    userid = models.CharField(primary_key=True,unique=True,max_length=6,default='')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.CharField(max_length=200)
    canSee = models.BooleanField(default=True)
    canRate = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    current_rating = models.PositiveIntegerField(MaxValueValidator(10),default=0)
    cumulated_rating = models.PositiveIntegerField(MaxValueValidator(10),default=0)

    public_key=models.TextField()     #user public key
    ratings_given=models.TextField()    #list of ratings given(encrypted)

    def __str__(self):
        return self.userid


    def update_ratings(self):
        tnow = datetime.datetime.now()
        rl = Rating.objects.all().filter(user2 = self.userid) # ratings to our user


        totalRatings = 0
        cum_rating = 0.0
        recentRatings = 0
        cur_rating = 0.0

        for r in rl :
            rate=int(r.rating)
            cum_rating+=rate
            totalRatings += 1
            try:
                tbuff = ((Control.objects.all().order_by('-updated_at'))[0]).TimeBufferForCalc
            except:
                tbuff = 7 * 86400

            if abs( r.created_at.timestamp() - tnow.timestamp() ) <= tbuff :
                #cur_rating += r.rating
                cur_rating+=rate
                recentRatings += 1
        try : # if Divide by zero because of no ratings ?
            self.current_rating   = (int)(cur_rating / recentRatings)
            self.cumulated_rating = (int)(cum_rating / totalRatings )
        except :
            self.current_rating   = 0
            self.cumulated_rating = 0

        #self.canSee is set/unset by EveryoneCanSee field in Control model only, hence next block of code is commented out

        # if Rating.objects.all().filter(user1 = self.userid).count() < (User.objects.all().exclude(is_superuser=True).count()-1 ):
        #     self.canSee = False
        # else :
        #     self.canSee = True

    def get_absolute_url(self):
        return ("/user/"+self.userid)

    def get_latest_work(self):
        works = Work.objects.filter(user=self).order_by('-updated_at').values('work')
        trueworks=[]
        for i in works:
            m=i.get('work')
            trueworks.append(m)
        works=trueworks
        try:
            latest_work = works[0]
            decrypted_work=signing.loads(latest_work)
            return decrypted_work[0]
        except:
            return None

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance,userid=instance.username)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

class Rating(models.Model):
    #user2 is the reviewee
    user2  = models.ForeignKey(Profile,on_delete=models.CASCADE,related_name='Profile2')
    
    rating=models.CharField(max_length=100) 
    
    #Field to be stored encrypted by public key of reviewer
    review = models.TextField()
    
    #Field to be stored encrypted by public key of reviewee
    review2 = models.TextField()
    
    canEdit = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return ("Anonymous rated " + self.user2.userid)

class Work(models.Model):
    user = models.ForeignKey(Profile,on_delete=models.CASCADE)
    work = models.CharField(max_length=500,blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.work

class Control(models.Model):
    SessionNumber = models.IntegerField(default=0)
    # CHOICES=[( True ,'Enable'), # Make strings if True and False naievly doesn't work
    #         (False,'Disable')]

    RegistrationEnabled = models.BooleanField(default=True)
    EveryoneCanSee  = models.BooleanField(default=True)
    EveryoneCanRate = models.BooleanField(default=True)
    EveryoneCanEdit = models.BooleanField(default=True)
    UpdateEveryone  = models.BooleanField(default=True)
    TimeBufferForCalc = models.IntegerField(default=(7*86400))
    TimeLimitForRatingEdits = models.IntegerField(default=(2*86400))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def updateOthers(self):
        userlist = Profile.objects.all()
        for user in  userlist:
            user.canSee  = self.EveryoneCanSee
            user.canRate = self.EveryoneCanRate
            if self.UpdateEveryone :
                user.update_ratings()
            user.save()

        ratings = Rating.objects.all()
        tnow = datetime.datetime.now()

        for rating in ratings :
            # find a better way than this because without
            print ( abs ( rating.created_at.timestamp() - tnow.timestamp() ) )
            if abs ( rating.created_at.timestamp() - tnow.timestamp() ) <= self.TimeLimitForRatingEdits :
                rating.canEdit = self.EveryoneCanEdit
                rating.save()

    def __str__(self):
        return ("Session Number:" + self.number)
