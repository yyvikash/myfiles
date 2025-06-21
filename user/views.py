from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,FileResponse,Http404
from .models import *
from convert.models import *
import os
from django.conf import settings
from django.db.models import Q
from datetime import date
from django.utils import timezone
from django.contrib import messages
# Create your views here.

def home(request):
    return render(request,"home.html")
    
def about(request):
     return render(request,"about.html")


def login(request):
    if request.method == "POST":
         email = request.POST.get("email")
         password = request.POST.get("password")
         remember = request.POST.get("remember_me")  # checkbox value
         user = tbl_users.objects.filter(Email=email,Password=password).first()
         if user:
              request.session['name']=(user.First_name)
              request.session['last_name']=(user.Last_name)
              request.session['email']=(user.Email)
              request.session['profile_pic']=str(user.Profile_pic)
              
              if not remember:
                request.session.set_expiry(0)  # expires on browser close
                # Else: keep default expiry (session persists until logout)

              return HttpResponse("<script>alert('Login successfully');window.location.href='/dashboard/';</script>")
         else:
              return HttpResponse("<script>alert('Invalid email or password');window.location.href='/login/';</script>")
    return render(request,"login.html")
    


def profile(request):
    if not request.session.get('email'):
        return redirect('login')

    user = tbl_users.objects.get(Email=request.session['email'])

    if request.method == 'POST':
        user.First_name = request.POST.get('first_name')
        user.Last_name = request.POST.get('last_name')
        user.Mobile = request.POST.get('mobile')

        if request.FILES.get('profile_pic'):
            user.Profile_pic = request.FILES['profile_pic']

        user.save()
        request.session['name'] = user.First_name
        request.session['last_name'] = user.Last_name
        request.session['profile_pic'] = str(user.Profile_pic)

        return redirect('profile')  # Refresh the page to show updated data

    return render(request, 'profile.html', {'user': user})


def logout(request):
     del request.session['name']
     del request.session['email']
     del request.session['profile_pic']
     return HttpResponse("<script>alert('Logout successfully');window.location.href='/';</script>")


def signup(request):
        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            mobile = request.POST.get('mobile')
            password = request.POST.get('password')
            profile_pic = request.FILES.get('profile_pic')  # 👈 File handling
            todayDate = date.today()

            if tbl_users.objects.filter(Email=email).exists():
                return HttpResponse("<script>alert('Email already registered');window.location.href='/login/';</script>")

            tbl_users(
                First_name=first_name,
                Last_name=last_name,
                Email=email,
                Mobile=mobile,
                Password=password,
                Profile_pic=profile_pic,
                Reg_date = todayDate
            ).save()
            return HttpResponse("<script>alert('Registered successfully');window.location.href='/login/';</script>")
        return render(request,"signup.html")


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        ContactMessage.objects.create(
            Name=name,
            Email=email,
            Subject=subject,
            Message=message,
            Date=timezone.now()
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect('contact')  # Make sure your URL is named 'contact'

    return render(request, 'contact.html')


def dashboard(request):
    if not request.session.get("email"):
        return HttpResponse("<script>alert('Please login to your account');window.location.href='/login/';</script>")

    user = tbl_users.objects.filter(Email=request.session.get("email")).first()
    user_files = tbl_files.objects.filter(Email=user).order_by("-id")[:5]

    # Pop upload_success message from session if available
    upload_success = request.session.pop('upload_success', None)

    return render(request, "dashboard.html", {
        "user": user,
        "user_files": user_files,
        "upload_success": upload_success
    })
     

     

def secure_download(request, file_id):
    try:
        file_obj = tbl_files.objects.get(id=file_id)

        # Optional: restrict access to logged-in user's files
        if request.session.get('email') != str(file_obj.Email):
            return HttpResponse("Unauthorized", status=401)

        file_path = file_obj.File.path  # Full path to the file
        file_name = os.path.basename(file_path)

        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)
            return response
        else:
            raise Http404("File not found")

    except tbl_files.DoesNotExist:
        raise Http404("File not found")


def all_files(request):
    if not request.session.get("email"):
        return redirect("login")

    user = tbl_users.objects.filter(Email=request.session.get("email")).first()
    files = tbl_files.objects.filter(Email=user)

    # 🔍 Filtering logic
    query = request.GET.get('q')
    date = request.GET.get('date')

    if query:
        files = files.filter(Q(File_Name__icontains=query) | Q(File_Type__icontains=query))
    if date:
        files = files.filter(Upload_Date=date)

    files = files.order_by("-Upload_Date")
    return render(request, "all_files.html", {"files": files})
    

def features(request):
    return render(request,"features.html")



def delete_file(request, file_id):
    file = get_object_or_404(tbl_files, id=file_id)
    user_email = request.session.get('email')

    # Optional: You may want to print or log this check
    if str(file.Email) == user_email:
        file.delete()

    return redirect('dashboard')  # or your actual dashboard URL name


def change_password(request):
    if not request.session.get("email"):
        return redirect("login")

    user = tbl_users.objects.get(Email=request.session["email"])

    if request.method == "POST":
        current = request.POST["current_password"]
        new = request.POST["new_password"]
        confirm = request.POST["confirm_password"]

        if current != user.Password:
            return render(request, "change_password.html", {"error": "Current password is incorrect."})
        elif new != confirm:
            return render(request, "change_password.html", {"error": "New passwords do not match."})
        elif len(new) < 6:
            return render(request, "change_password.html", {"error": "New password must be at least 6 characters."})
        else:
            user.Password = new
            user.save()
            return render(request, "change_password.html", {"success": "Password changed successfully."})

    return render(request, "change_password.html")


def forget_password(request):
    return HttpResponse("<script>alert('This feature is in progress. This time you can fill contact us form, The password will be sent to your gmail');window.location.href='/contact/';</script>")