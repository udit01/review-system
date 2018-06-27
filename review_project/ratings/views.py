from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login
from django.views import generic
from django.views.generic import View
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from . import models
from . import forms
import datetime
from django.core import signing


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
        ratercansee = request.user.profile.canSee
        logged_in=True
        return render(request, self.template_name, {'object_list':object_list,'ratercansee':ratercansee,'logged_in':logged_in})

    # def get_context_data(self, **kwargs):
    #     ctx = super(LeaderBoardView, self).get_context_data(**kwargs)
    #     ctx['ratercansee'] = self.get_object().date.strftime("%B")
    #     return ctx

class RegisterView(View):
    form_class_profile = forms.ProfileForm
    template_name = 'registration/login.html'

    def get(self,request):
        logged_in=False
        form_profile = self.form_class_profile(None)
        return render(request, self.template_name, {'form':form_profile,"type":"Register",'logged_in':logged_in})

    def post(self,request):
        logged_in=False
        print ("Received Post Request")
        form_profile = self.form_class_profile(request.POST)

        if form_profile.is_valid():
            user = form_profile.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.about = form_profile.cleaned_data.get('about')
            user.save()
            raw_password = form_profile.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            print (user.username)
            login(request, user)
            print ("Logged in")
            return redirect('ratings:index')
        else:
            return render(request, self.template_name, {'form':form_profile,"type":"Register",'logged_in':logged_in})

class UserUpdate(generic.UpdateView):
    model = models.Profile
    fields = ['name','about','updated_at','work']

########################################## Do @ superuserloginrequired here ###################################
class SudoView(View):
    form_class = forms.SudoForm
    template_name = 'registration/login.html'
    # Add user id to session variables
    @method_decorator(user_passes_test(lambda u: u.is_superuser,login_url='/login/'))
    def get(self,request):
        logged_in=True
        try :
            ctrl = (models.Control.objects.all().order_by('-updated_at'))[0]
        except :
            ctrl = models.Control()

        form = self.form_class(instance=ctrl)

        return render(request, self.template_name, {'logged_in':logged_in,'form':form, 'type':"Sudo"})

    @method_decorator(user_passes_test(lambda u: u.is_superuser,login_url='/login/'))
    def post(self,request):
        form = self.form_class(request.POST)
        logged_in=True
        if form.is_valid() :
            SessionNumber=form.cleaned_data['SessionNumber']
            # commit = False ?
            try:
                ctrl = (models.Control.objects.all().order_by('-updated_at'))[0]
                if ctrl.SessionNumber==SessionNumber: #Don't create new query object, instead change the current
                    ctrl.RegistrationEnabled=form.cleaned_data['RegistrationEnabled']
                    ctrl.EveryoneCanSee=form.cleaned_data['EveryoneCanSee']
                    ctrl.EveryoneCanRate=form.cleaned_data['EveryoneCanRate']
                    ctrl.EveryoneCanEdit=form.cleaned_data['EveryoneCanEdit']
                    ctrl.UpdateEveryone=form.cleaned_data['UpdateEveryone']
                else:
                    RegistrationEnabled=form.cleaned_data['RegistrationEnabled']
                    EveryoneCanSee=form.cleaned_data['EveryoneCanSee']
                    EveryoneCanRate=form.cleaned_data['EveryoneCanRate']
                    EveryoneCanEdit=form.cleaned_data['EveryoneCanEdit']
                    UpdateEveryone=form.cleaned_data['UpdateEveryone']
                    new_ctrl=models.Control(SessionNumber=SessionNumber,RegistrationEnabled=RegistrationEnabled,
                    EveryoneCanSee=EveryoneCanSee,EveryoneCanEdit=EveryoneCanEdit,EveryoneCanRate=EveryoneCanRate,
                    UpdateEveryone=UpdateEveryone)
                    ctrl=new_ctrl
            except:
                RegistrationEnabled=form.cleaned_data['RegistrationEnabled']
                EveryoneCanSee=form.cleaned_data['EveryoneCanSee']
                EveryoneCanRate=form.cleaned_data['EveryoneCanRate']
                EveryoneCanEdit=form.cleaned_data['EveryoneCanEdit']
                UpdateEveryone=form.cleaned_data['UpdateEveryone']
                new_ctrl=models.Control(SessionNumber=SessionNumber,RegistrationEnabled=RegistrationEnabled,
                EveryoneCanSee=EveryoneCanSee,EveryoneCanEdit=EveryoneCanEdit,EveryoneCanRate=EveryoneCanRate,
                UpdateEveryone=UpdateEveryone)
                ctrl=new_ctrl
            ctrl.updateOthers()
            ctrl.save()
            # idk why but just do it
            return redirect(self.request.path_info)
        else :
            # print (form)
            return render(request, self.template_name, {'logged_in':logged_in,'form':form, 'type':"Sudo", 'error_message': "Your Sudo form wasn't valid."})


class UserDetailView(generic.DetailView):
    form_class = forms.RatingForm
    form_class_work = forms.WorkForm
    form_class_update = forms.UserUpdateForm
    template_name = 'ratings/user.html'

    def get(self, request,**kwargs):
        logged_in=True

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

        uid = kwargs['uid'] # target user
        if request.user :
            raterid = request.user.profile.userid
            ratingFound = False
            try:
                user = models.Profile.objects.get(userid=uid)
                target_user = models.User.objects.get(username=uid)
                full_name = target_user.first_name + " " + target_user.last_name
            except ObjectDoesNotExist:
                return render(request, error_template ,{'error': "The User with User Id : "+ uid +" does not exist."})
            try:
                ratings = models.Rating.objects.all().filter(user1=raterid).filter(user2=user).order_by('-updated_at')
                reviews=decrypt(ratings,'review')
                ratings = decrypt(ratings,'rating')


                #ratings.append('lol')
                #Have to decrypt it to show to the user.

            except ObjectDoesNotExist:
                current_rating = "Not yet rated by you. Rating Object after these filters doesn't exist."
            try:
                current_rating = ratings[0]
                current_review = reviews[0]
                ratingFound = True
            except :
                current_rating = "Not yet reviewed by you."
                current_review="Not yet reviewed by you"
            try :
                works_together=[]
                works = models.Work.objects.all().filter(user=user).order_by('-updated_at')#.values('work')
                works=decrypt(works) # Works now consist of a list of decrypted works
            except :
                works = None
            for t in range(len(works)): # starting part of the works will be grouped togetheer into a new list of dictionaries
                j=works[t].split()
                if len(j)>5:
                    start=""
                    for m in range(4):
                        start+=j[m]+" "
                    start=start.rstrip(" ")
                    start+="..."
                else:
                    start=works[t]
                works_together.append({'start':start,'work':works[t]})
            rater = models.Profile.objects.get(userid = raterid)
            if rater.canRate :
                form = self.form_class(None)
            else  :
                form = None
            # Get User Update Forms
            if raterid == uid : #If on your own profile
                form_work = self.form_class_work(None)
                form_update = self.form_class_update(initial={'about':rater.about})
            else :
                form_work = None
                form_update = None

            ratingFound = False if (uid == raterid) else ratingFound  #If on your own profile
            current = True if (uid == raterid) else False   #If on your own profile
            together = []
            if(current):
                curr_ratings = models.Rating.objects.filter(user2=rater).order_by('-updated_at')
                sessions=[]
                for j in range(len(curr_ratings)):
                    sessions.append((curr_ratings[j]).get_session_number)
                try:
                    reviews=decrypt(curr_ratings,'review')
                    ratings = decrypt(curr_ratings,'rating')
                except:
                    reviews=None
                    ratings=None
                for j in range(len(reviews)):
                    together.append({'rating':ratings[j],'review':reviews[j],'session':sessions[j]})


            return render(request, self.template_name, {'logged_in':logged_in,'works_together':works_together, 'user':user, 'name':full_name, 'current':current, 'current_rated':current_rating, 'works': works, 'ratingFound':ratingFound, 'form':form, 'workform':form_work, 'updateform':form_update, 'together':together, 'rater':rater,'current_review':current_review})

        else:
            try :
                user = models.Profile.objects.get(userid=uid)
                target_user = models.User.objects.get(username=uid)
                full_name = target_user.first_name + " " + target_user.last_name
            except ObjectDoesNotExist :
                return render(request, error_template ,{'error': "The User with User Id : "+ uid +" does not exist."})
            try :
                works_together=[]
                works = models.Work.objects.all().filter(user=user).order_by('-updated_at')#.values('work')
                works=decrypt(works)

            except :
                works = None
            for t in range(len(works)): # starting part of the works will be grouped togetheer into a new list of dictionaries
                j=works[t].split()
                if len(j)>5:
                    start=""
                    for m in range(4):
                        start+=j[m]+" "
                    start=start.rstrip(" ")
                    start+="..."
                else:
                    start=works[t]
                works_together.append({'start':start,'work':works[t]})

            return render(request, self.template_name, {'logged_in':logged_in,'works_together':works_together, 'user':user, 'name':full_name, 'current':False, 'works':works})#,'decryptworks':decryptworks})

    def post(self, request, **kwargs):
        form = self.form_class(request.POST)
        workform = self.form_class_work(request.POST)
        updateform = self.form_class_update(request.POST)
        logged_in=True
        # avoid insecure access through postman
        try:
            target = models.Profile.objects.get(userid = kwargs['uid'])
            target_user = models.User.objects.get(username = kwargs['uid'])
            full_name = target_user.first_name + " " + target_user.last_name
        except:
            return render(request, error_template ,{'error': "Invalid Post Request."})
        if request.user :
            if form.is_valid() :
                rnum = form.cleaned_data['rating']
                rev = form.cleaned_data['review']
                encryptedreview=signing.dumps((rev,))
                rater = models.Profile.objects.get(userid = request.user.profile.userid)
                full_name = target_user.first_name + " " + target_user.last_name
                if kwargs['uid'] == None :
                    return render( request, self.template_name , {'error_message': "Invalid User", 'form':form, 'user':target, 'name':full_name} )
                elif kwargs['uid'] == request.user.profile.userid :
                    return render( request, self.template_name , {'error_message': "You cannot rate yourself.", 'form':form, 'user':target, 'name':full_name} )
                else :
                    f = True
                    try:
                        ratings = models.Rating.objects.all().filter(user1=rater).filter(user2=target).order_by('-updated_at')
                        robj = ratings[0]
                        if (not robj.canEdit) :
                            f = False
                    except :
                        f = False

                    if f :
                        robj.rating = rnum
                        robj.review = encryptedreview
                    else :
                        robj = models.Rating(user1 = rater,
                                            user2 = target,
                                            rating=rnum,review=encryptedreview, canEdit = True)
                    robj.save()
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
            elif updateform.is_valid() :
                about = updateform.cleaned_data['about']
                user = models.Profile.objects.get(userid = request.user.profile.userid)
                user.about = about
                user.save()
                return redirect(self.request.path_info)
            else :
                # print (request.session['user_id'])
                return render( request, self.template_name , {'error_message': "Ratings form wan't valid.", 'form':form, 'user':target_user, 'name':full_name} )
        else :
            return render( request, login_template , {'error_message': "You have to be logged in to rate.", 'form':form, 'user':target_user, 'name':full_name} )
    # Get ratings for this user, rated by the session user
    # Edit the user details if the user id of the current view is the same as the session user
    # Edit the work details if the user id of the current view is the same as the session user

    # Function to check if the user id of the current view is the same as the session user
    def is_same_user(self,request):
        if request.user:
            user = models.User.objects.get(userid=request.GET.get('user','None'))
            return (user.userid==request.user.profile.userid)
        else:
            return False






#  For Udit
#  ---------------------------------Redundant Classes-------------------------------------
# class LoginView(View):
#     form_class = forms.LoginForm
#     template_name = 'ratings/login.html'
#     # Add user id to session variables
#     def get(self,request):
#         form = self.form_class(None)
#         return render(request, self.template_name, {'form':form})
# print("-----------------------------------------------------")
# print (form) # this turned out to be null
# # print (form.cleaned_data)
# # print (form.cleaned_data['userid'])
# # print (form.cleaned_data['password'])

# if form.is_valid() :
#     # form.save()
#     uid = form.cleaned_data['userid']
#     paswd = form.cleaned_data['password']
#     try:
#         uobj = models.User.objects.get(userid=uid)
#         if(uobj):
#             if(uobj.password == paswd) :
#                 request.session['user_id'] = form.cleaned_data['userid']
#                 return redirect('ratings:index')
#             else :
#                 return render(request, self.template_name, {'form': form ,'error_message': "Password doesn't match","type":"Login"})
#         else :
#             return render(request, self.template_name, {'form': form ,'error_message': "User doesn't exist.","type":"Login"})
#     except ObjectDoesNotExist :
#         return render(request, self.template_name, { 'form': form ,'error_message': "User ID doesn't exist.","type":"Login"})

#     return redirect('ratings:index')
# else :
#     print("-----------------------------------------------------")
#     print (form)
#     # print (request.session['user_id'])
#     return redirect('ratings:login')

# class LogoutView(View):
#     def get(self, request):
#         try:
#             if request.session['user_id']:
#                 del request.session['user_id']
#         except Exception:
#             pass
#         return redirect('ratings:login')

# class RegisterView(View):
#     form_class = forms.UserForm
#     template_name = 'ratings/login.html'
#     # Add user id to session variables
#     def get(self,request):
#         form = self.form_class(None)
#         return render(request, self.template_name, {'form':form,'type':"Register"})

#     def post(self,request):
#         form = self.form_class(request.POST)

#         if form.is_valid() :
#             # form.save()
#             fd = form.cleaned_data
#             uobj = models.User(name=fd['name'],userid=fd['userid'],about=fd['about'],
#                                 password=fd['password'],canSee=False,canRate=True)
#             uobj.save()
#             request.session['user_id'] = fd['userid']
#             return redirect('ratings:index')
#         else :
#             return redirect('ratings:register')

#     def post(self,request):
#         username = request.POST['username']
#         password = request.POST['password']
#         print (username)
#         print (password)
#         user = User.objects.filter(username=request.POST['username'],password=request.POST['password'])
#         if (user is not None):
#             login(request,user)
#             return redirect('ratings:index')
#         else:
#             print ("User is not found")
#             return redirect('ratings:login')

# class LogoutView(View):
#     def get(self, request):
#         logout(request)
#         return redirect('ratings:user_list')
