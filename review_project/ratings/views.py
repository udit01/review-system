from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.views import generic
from django.views.generic import View
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core import signing

from . import models
from . import forms
from . import encryption

import datetime


error_template = 'ratings/error.html'
login_template = 'registration/login.html'

# SESSION_NUMBER = 0

# Create your views here.
# @login_required(login_url='/login/')
class IndexView(generic.ListView):
    #if logged in, display the current user's details
    @method_decorator(login_required)
    def get(self, request):
        template_name = 'ratings/user.html'
        user = request.user

        try:
            current_user = models.Profile.objects.get(userid=user.profile.userid)
        except ObjectDoesNotExist:
            return render(request, error_template ,{'error': "The User for user_id : "+user.profile.userid+" DoesNotExist. "})
        # return render(request, template_name, {'user':current_user , 'current':True})
        return redirect('/user/'+user.profile.userid)

class LeaderBoardView(View):
    template_name = 'ratings/profile_list.html'

    @method_decorator(login_required)
    def get(self,request):
        object_list = models.Profile.objects.all().order_by('-current_rating')
        #ln=0
        #lst=[]
        ratercansee = request.user.profile.can_see
        logged_in=True
        loshortworks=[]

        curr_control = models.Control.objects.latest('updated_at')

        for i in object_list:
            latest_work = i.get_latest_work()
            try:
                if len(latest_work)>40:
                    loshortworks.append(latest_work[:40])
                else:
                    loshortworks.append(None)
            except:
                loshortworks.append(latest_work)
        dict =[]
        for j in range(len(object_list)):
            if object_list[j].user.is_superuser:
                continue
            else:
                robjs = models.Rating.objects.all().filter(session_number = curr_control.session_number).filter(user1=request.user.profile).filter(user2=object_list[j])

                rated = False if list(robjs) == [] else True
                if (request.user.profile == object_list[j]):
                    rated = True
                ele = {'profile':object_list[j],'short':loshortworks[j], 'unrated':not rated}
                dict.append(ele)


        return render(request, self.template_name, {'dict':dict,'object_list':object_list,'ratercansee':ratercansee,'logged_in':logged_in,'loshortworks':loshortworks,})

    # def get_context_data(self, **kwargs):
    #     ctx = super(LeaderBoardView, self).get_context_data(**kwargs)
    #     ctx['ratercansee'] = self.get_object().date.strftime("%B")
    #     return ctx

class RegisterView(View):
    form_class_profile = forms.ProfileForm
    template_name = 'registration/login.html'
    logged_in = False

    def get(self,request):
        # Assume the control object is available
        ctrl_latest = models.Control.objects.latest('updated_at')
        # Don't send a form profie if registration is disabled
        registration = ctrl_latest.registration_enabled
        form_profile = self.form_class_profile(None) if registration else None

        return render(request, self.template_name, {'form':form_profile, "type":"Register", 'logged_in':self.logged_in, 'registration':registration})

    def post(self,request):
        form_profile = self.form_class_profile(request.POST)

        if form_profile.is_valid():
            user = form_profile.save()
            raw_password = form_profile.cleaned_data.get('password1')
            user.refresh_from_db()  # load the profile instance created by the signal
            key = encryption.generate_key(raw_password,b"hackfest")
            user.profile.public_key = key.publickey().exportKey().decode('utf-8')
            user.profile.about = form_profile.cleaned_data.get('about')
            user.save()
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            request.session['private_key'] = key.exportKey().decode('utf-8')
            return redirect('ratings:index')
        else:
            return render(request, self.template_name, {'form':form_profile,"type":"Register",'logged_in':self.logged_in})

class UserUpdate(generic.UpdateView):
    model = models.Profile
    fields = ['name', 'about', 'updated_at', 'work']

########################################## Do @ superuserloginrequired here ###################################
class SudoView(View):
    form_class = forms.SudoForm
    template_name = 'registration/login.html'
    logged_in = True

    # Add user id to session variables
    @method_decorator(user_passes_test(lambda u: u.is_superuser,login_url='/login/'))
    def get(self, request):
        try :
            ctrl = (models.Control.objects.all().order_by('-updated_at'))[0]
            registration = ctrl.RegistrationEnabled
        except :
            ctrl = models.Control()
            registration = True
        form = self.form_class(instance=ctrl)

        return render(request, self.template_name, {'registration':registration, 'logged_in':self.logged_in, 'form':form, 'type':"Sudo"})

    @method_decorator(user_passes_test(lambda u: u.is_superuser, login_url='/login/'))
    def post(self,request):
        form = self.form_class(request.POST)

        if form.is_valid() :
            SessionNumber = form.cleaned_data['session_number']
            # commit = False ?

            latest_ctrl = models.Control.objects.latest('updated_at')

            #if same SessionNumber,then delete current object and create new
            if (latest_ctrl is not None) and (SessionNumber == latest_ctrl.session_number):
                latest_ctrl.delete()

            registration_enabled = form.cleaned_data['registration_enabled']
            everyone_can_rate = form.cleaned_data['everyone_can_rate']
            everyone_can_edit = form.cleaned_data['everyone_can_edit']
            update_everyone = form.cleaned_data['update_everyone']

            ctrl = models.Control(session_number=SessionNumber, registration_enabled=registration_enabled,
            everyone_can_edit=everyone_can_edit, everyone_can_rate=everyone_can_rate, update_everyone=update_everyone)

            ctrl.save()

            # idk why but just do it
            return redirect(self.request.path_info)
        else :
            return render(request, self.template_name, {'logged_in':self.logged_in, 'form':form, 'type':"Sudo", 'error_message': "Your Sudo form wasn't valid."})


class UserDetailView(generic.DetailView):
    form_class = forms.RatingForm
    form_class_work = forms.WorkForm
    form_class_update = forms.UserUpdateForm
    template_name = 'ratings/user.html'

    @method_decorator(login_required)
    def get(self, request, **kwargs):
        logged_in = True

        def decrypt(encryptedqueryset, string='work'):
            dictionary = encryptedqueryset.values(string)
            trueworks = []
            for i in dictionary:
                m = i.get(string)
                trueworks.append(m)
            decryptworks = []
            for i in trueworks:
                n = signing.loads(i)
                decryptworks.append(n[0])
            return decryptworks

        uid = kwargs['uid'] # target user
        if request.user:
            raterid = request.user.profile.userid
            try:
                user_profile = models.Profile.objects.get(userid=uid)
                user = models.User.objects.get(username=uid)
                full_name = user.first_name + " " + user.last_name
            except ObjectDoesNotExist:
                # Invalid username in get request
                return render(request, error_template, {'error': "The User with User Id : "+ uid +" does not exist."})

            try:
                ratings = models.Rating.objects.all().filter(user1=raterid).filter(user2=user_profile).order_by('-updated_at')
                curr_control = models.Control.objects.latest('updated_at')
                robj = ratings[0]
                # print(str(curr_control.session_number) + " " + str(robj.session_number)) # Debug
                if curr_control.session_number == robj.session_number:
                    current_rating = signing.loads(encryption.decode(robj.rating, request.session['private_key']))[0]
                    current_review = encryption.decode(robj.review, request.session['private_key'])
                else:
                    raise Exception
            except:
                # print("Either first time rate or no rating in present session") # Debug
                current_rating = "Not yet reviewed by you."
                current_review = "Not yet reviewed by you."

            try:
                works = models.Work.objects.all().filter(user=user_profile).order_by('-updated_at') #.values('work')
                decrypted_works = decrypt(works) # Works now consist of a list of decrypted works
            except:
                decrypted_works = None

            rater = models.Profile.objects.get(userid=raterid)
            if rater.can_rate:
                form = self.form_class(None)
            else:
                form = None

            # Get User Update Forms
            form_work = self.form_class_work(None) if (uid == raterid) else None
            form_update = self.form_class_update(initial={'about':rater.about}) if (uid == raterid) else None
            current = True if (uid == raterid) else False   # If on your own profile

            all_ratings = []
            if(current and rater.can_see):
                curr_ratings = models.Rating.objects.filter(user2=rater).order_by('-updated_at')
                try:
                    reviews = curr_ratings.values('review2')
                    ratings = curr_ratings.values('rating2')
                    for j in range(len(reviews)):
                        rating = signing.loads(encryption.decode(ratings[j]['rating2'], request.session['private_key']))[0]
                        review = encryption.decode(reviews[j]['review2'], request.session['private_key'])
                        all_ratings.append({'rating':rating, 'review':review})
                        print(all_ratings)
                except:
                    reviews = None
                    ratings = None

            return render(request, self.template_name, {'logged_in':True, 'works_together':decrypted_works, 'user':user_profile, 'name':full_name, 'current':current, 'current_rated':current_rating, 'form':form, 'workform':form_work, 'updateform':form_update, 'together':all_ratings, 'rater':rater,'current_review':current_review})
        else:
            return render(request, error_template, {'error': "No such user exists. Please validate your request."})


    @method_decorator(login_required)
    def post(self, request, **kwargs):
        form = self.form_class(request.POST)
        workform = self.form_class_work(request.POST)
        updateform = self.form_class_update(request.POST)
        logged_in = True
        # avoid insecure access through postman
        try:
            target = models.Profile.objects.get(userid=kwargs['uid'])
            target_user = models.User.objects.get(username=kwargs['uid'])
            full_name = target_user.first_name + " " + target_user.last_name
        except:
            return render(request, error_template, {'error': "Invalid Post Request."})

        if request.user:
            if form.is_valid():
                rating = form.cleaned_data['rating']
                review = form.cleaned_data['review']

                pub_key = request.user.profile.public_key
                pub_key2 = target.public_key
                enc_rating = encryption.encrypt(rating, pub_key)
                enc_review = encryption.encrypt(review, pub_key)
                enc_rating2 = encryption.encrypt(rating, pub_key2)
                enc_review2 = encryption.encrypt(review, pub_key2)

                rater = models.Profile.objects.get(userid=request.user.profile.userid)
                # print(rater) # Debug
                # print(target) # Debug
                if kwargs['uid'] == None:
                    err = "Invalid User"
                elif kwargs['uid'] == request.user.profile.userid:
                    err = "You cannot rate yourself."
                else:
                    editRating, newRating = True, True
                    curr_session = models.Control.objects.latest('updated_at')

                    # print("Current session number: " + str(curr_session.session_number)) # Debug
                    try:
                        robj = models.Rating.objects.all().filter(user1=rater).filter(user2=target).order_by('-updated_at')[0]
                        # print(robj) # Debug
                        # print(curr_session.session_number) # Debug
                        if curr_session.session_number == robj.session_number:
                            newRating = False
                        if (curr_session.session_number == robj.session_number) and (not robj.can_edit):
                            editRating = False
                    except:
                        # print("Could not find rating object") # Debug
                        editRating = False

                    # print(str(newRating) + " " + str(editRating)) # Debug
                    # Update rating object
                    if newRating:
                        robj = models.Rating(user1=rater, user2=target, rating=enc_rating, review=enc_review, 
                                            rating2=enc_rating2, review2=enc_review2, can_edit=True, session_number=curr_session.session_number)
                    elif editRating:
                        robj.rating = enc_rating
                        robj.review = enc_review
                        robj.rating2 = enc_rating2
                        robj.review2 = enc_review2
                    robj.save()
                    target.updateMyRating(signing.loads(rating)[0], curr_session.session_number)
                    rater.update_can_see(curr_session.session_number)

                    return redirect(self.request.path_info)
                return render(request, self.template_name, {'error_message': err, 'form':form, 'user':target, 'name':full_name})

            elif updateform.is_valid():
                about = updateform.cleaned_data['about']
                user = models.Profile.objects.get(userid=request.user.profile.userid)
                user.about = about
                user.save()
                return redirect(self.request.path_info)

            elif workform.is_valid() :
                onlychoices=request.POST.getlist('working[]') # Returns list of selected checkbox(decrypted)
                work = workform.cleaned_data['work']
                tupwork= (work,)
                cryptotuple=signing.dumps(tupwork)
                #decryptotuple=signing.loads(cryptotuple)
                user = models.Profile.objects.get(userid = request.user.profile.userid)

                if work:
                    new_work = models.Work(user = user, work = cryptotuple)
                    new_work.save()
                if onlychoices:
                    for each_delete in onlychoices:
                        r=models.Work.objects.filter(user=user)
                        works=r.values('work')
                        trueworks=[]
                        for i in works:
                            m=i.get('work')
                            trueworks.append(m)
                        works=trueworks
                        for i in range(len(works)):
                            n=signing.loads(works[i])
                            if each_delete==n[0]:
                                r[i].delete()
                                break
                return redirect(self.request.path_info)

            else :
                # print (request.session['user_id'])
                return render(request, self.template_name, {'error_message': "Ratings form wan't valid.", 'form':form, 'user':target_user, 'name':full_name} )
        else:
            return render(request, login_template, {'error_message': "You have to be logged in to rate.", 'form':form, 'user':target_user, 'name':full_name} )

class EditView(generic.DetailView):
    form_class_work = forms.WorkForm
    form_class_update = forms.UserUpdateForm
    template_name = 'ratings/edit.html'

    @method_decorator(login_required)
    def get(self,request, **kwargs):

        def decrypt(encryptedqueryset, string='work'):
            dictionary = encryptedqueryset.values(string)
            trueworks = []
            for i in dictionary:
                m = i.get(string)
                trueworks.append(m)
            decryptworks = []
            for i in trueworks:
                n = signing.loads(i)
                decryptworks.append(n[0])
            return decryptworks

        try:
            user = request.user      #The logged in user
            user_profile = models.Profile.objects.get(userid = user.profile.userid)
        except:
            return render(request,error_template,{'error':'Invalid User.'})
        try:
            works = models.Work.objects.all().filter(user=user_profile).order_by('-updated_at') #.values('work')
            decrypted_works = decrypt(works) # Works now consist of a list of decrypted works
        except:
            decrypted_works = None

        form_work = self.form_class_work(None)
        form_update = self.form_class_update(initial={'about':user_profile.about})
        return render(request,self.template_name,{'user':user_profile,'workform':form_work,'updateform':form_update,'works':decrypted_works})

    def post(self,request, **kwargs):

        def decrypt(encryptedqueryset, string='work'):
            dictionary = encryptedqueryset.values(string)
            trueworks = []
            for i in dictionary:
                m = i.get(string)
                trueworks.append(m)
            decryptworks = []
            for i in trueworks:
                n = signing.loads(i)
                decryptworks.append(n[0])
            return decryptworks

        form_work = self.form_class_work(request.POST)
        form_update = self.form_class_update(request.POST)
        try:
            user = request.user      #The logged in user
            user_profile = models.Profile.objects.get(userid = user.profile.userid)
        except:
            pass
        del_work =  request.POST.get('work_delete')
        all_works = models.Work.objects.filter(user = user_profile)
        decrypted_works = decrypt(all_works)
        for index in range(len(decrypted_works)):
            if del_work == decrypted_works[index]:
                all_works[index].delete()
        #Add as required
        return render(request,self.template_name,{'workform':form_work,'updateform':form_update})

class LoginView(View):
    form_class = forms.LoginForm
    template_name = 'registration/login.html'
    # Add user id to session variables
    def get(self,request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form':form})
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid() :
            uid = form.cleaned_data['userid']
            paswd = form.cleaned_data['password']
            try:
                uobj = models.User.objects.get(username=uid)
                if(uobj):
                    user = authenticate(username = uid, password = paswd)
                    if user is not None:
                        if user.is_active:
                            login(request, user)
                            key = encryption.generate_key(paswd,b"hackfest")
                            request.session['private_key'] = key.exportKey().decode('utf-8')
                            request.session['user_id'] = form.cleaned_data['userid']
                        return redirect('ratings:index')
                    else :
                        return render(request, self.template_name, {'form': form ,'error_message': "Password doesn't match","type":"Login"})
                else :
                    return render(request, self.template_name, {'form': form ,'error_message': "User doesn't exist.","type":"Login"})
            except ObjectDoesNotExist :
                return render(request, self.template_name, { 'form': form ,'error_message': "User ID doesn't exist.","type":"Login"})
            return redirect('ratings:index')
        else :
            return redirect('ratings:login')

class LogoutView(View):
    def get(self, request):
        try:
            if request.session['user_id']:
                del request.session['user_id']
            if request.session['private_key']:
                del(request.session['private_key'])
        except Exception:
            pass
        return redirect('ratings:login')