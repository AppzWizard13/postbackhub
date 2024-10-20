from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views import View 
from django.views.generic import TemplateView
from account.forms import UserLoginForm
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib import auth, messages
from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm, UserForm
# User = get_user_model()  # Reference your custom user model
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import User




# Create your views here.
class HomePageView( TemplateView):
    template_name = "dashboard/authentication-login.html"


    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {}
        return context




class UserloginView(View):
    def get(self, request):
        template = "dashboard/authentication-login.html"
        context = {}
        context['form'] = UserLoginForm()
        logged_user = request.user
        if logged_user.is_authenticated:
            return redirect('dashboard')  # Redirect if already logged in
        else:
            return render(request, template, context)
        
    def post(self, request):
        context = {}
        form = UserLoginForm(request.POST)
        context['form'] = form
        template = "dashboard/authentication-login.html"

        if request.method == "POST" and form.is_valid():
            login_username = request.POST["username"]
            login_password = request.POST["password"]

            # Authenticate user using Django authentication
            user = auth.authenticate(username=login_username, password=login_password)
            if user:
                # Login the user via Django
                auth.login(request, user)

                # Now, initiate Fyers login flow
                # redirect_uri = settings.FYERS_REDIRECT_URL + "/dashboard"
                # client_id = settings.FYERS_APP_ID
                # secret_key = settings.FYERS_SECRET_ID

                # Or redirect the user to this URL within the app
                return redirect('dashboard')

            else:
                messages.error(request, 'Username or Password incorrect!')
                return render(request, template, context)

        return render(request, template, context)




class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = "dashboard/authentication-register.html"  # Create this template for the registration page
    success_url = reverse_lazy('login')  # Redirect to login page after successful registration

    def form_valid(self, form):
        # You can add any custom logic here if needed before saving the form
        return super().form_valid(form)



class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def dispatch(self, request, *args, **kwargs):

        # Call the parent class's dispatch method
        return super().dispatch(request, *args, **kwargs)

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect('login')  # Change 'login' to the name of your login URL

# Manage Users: List all users
class UserListView(ListView):
    model = User
    template_name = 'dashboard/user_list_view.html'  # Create a template for listing users
    context_object_name = 'users'
    
    def get_queryset(self):
        return User.objects.all()  # Customize this query if needed (e.g., filter active users)



# Manage Users: View details of a specific user
class UserDetailView(UpdateView):
    model = User
    template_name = 'dashboard/user-detail-edit.html'  # Ensure this template exists
    context_object_name = 'user'
    form_class = UserForm  # Use the custom form created above
    success_url = reverse_lazy('manage_user')  # Redirect after successful edit

    def form_valid(self, form):
        # Get the user data from the form
        user = form.save(commit=False)  # Don't commit the save yet
        
        # Prepare the data you want to update
        updated_data = {
            'email': form.cleaned_data.get('email'),
            'phone_number': form.cleaned_data.get('phone_number'),
            'role': form.cleaned_data.get('role'),
            'country': form.cleaned_data.get('country'),
            'dhan_access_token': form.cleaned_data.get('dhan_access_token'),
            'dhan_client_id': form.cleaned_data.get('dhan_client_id'),
            'status': form.cleaned_data.get('status'),
            'email': form.cleaned_data.get('email'),
            # 'profile_image': form.cleaned_data.get('profile_image'), # Include this if needed and make sure it's handled correctly
        }
        
        # Update the user fields in the User model where username matches
        User.objects.filter(username=user.username).update(**updated_data)

        # Add a success message and return the response
        messages.success(self.request, 'User details updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        print("oooooooooooooooooooooooooooooooooooooo")
        # Print form errors to console for debugging
        print(form.errors)  # This will output any validation errors in the console
        # messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_object(self, queryset=None):
        print("pppppppppppppppppppppppppppppppppppppp")
        # Fetch the user object based on the URL parameter (user ID)
        return get_object_or_404(User, pk=self.kwargs['pk'])  # Assuming you're using the user ID as a URL parameter
        
# Manage Controls: List view for controls
class ControlListView(ListView):
    template_name = 'control_list.html'  # Create a template for managing controls
    context_object_name = 'controls'

    def get_queryset(self):
        # Return controls (replace with your logic for controls)
        return []  # Modify this with appropriate control fetching logic


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

# Disable CSRF for the postback URL, as it might be a third-party service posting to this URL.
@csrf_exempt
def dhan_postback(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON data
            postback_data = json.loads(request.body)
            
            # Log or print the received data
            logging.info(f"Received Dhan postback: {postback_data}")
            print(f"Received Dhan postback: {postback_data}")
            
            # Do any further processing with the data here (e.g., save it to the database)
            # Example: extract specific fields from the postback_data
            dhan_client_id = postback_data.get("dhanClientId")
            order_id = postback_data.get("orderId")
            order_status = postback_data.get("orderStatus")

            if dhanClientId:
                UserObj = User.Objects.filter(dhan_client_id= dhanClientId).first()
                dhan_access_token = UserObj.dhan_access_token
                print("dhan_access_tokendhan_access_token", dhan_access_token)

            
            # (Optional) save data to a model if needed
            
            # Return a success response
            return JsonResponse({'status': 'success', 'message': 'Data received successfully'})
        
        except json.JSONDecodeError:
            # Handle JSON decoding errors
            logging.error("Invalid JSON received in postback")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        
    # If the request method is not POST, return a method not allowed error
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
