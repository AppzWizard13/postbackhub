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
from .forms import CustomUserCreationForm, UserForm, CustomControlCreationForm
User = get_user_model()  # Reference your custom user model
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404
from django.contrib import messages
import http.client  # Ensure the http.client module is imported
import json  # Import json for decoding the API response
from dhanhq import dhanhq

# from .models import User




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



class ControlCreateView(CreateView):
    model = User
    form_class = CustomControlCreationForm
    template_name = "dashboard/create_control.html"  # Create this template for the registration page
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


# Get the custom user model
User = get_user_model()

class UserListView(ListView):
    model = User  # This will now refer to the custom user model
    template_name = 'dashboard/user_list_view.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return User.objects.all()  # Optionally filter the users as per your requirements


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

        print("oooooooooooooooooooooooooooooooooooooo")

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
        
from django.views.generic import ListView
from .models import Control

class ControlListView(ListView):
    model = Control
    template_name = 'dashboard/control_listview.html'  # Your template file
    context_object_name = 'controls'

    def get_queryset(self):
        # Return the list of controls, fetch all or filter based on your logic
        return Control.objects.all()  # Or filter controls based on the user


from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import Control
from .forms import ControlForm  # Ensure you have a ControlForm created for your Control model

class EditControlView(UpdateView):
    model = Control
    template_name = 'dashboard/edit_control.html'  # Ensure this template exists
    context_object_name = 'control'
    form_class = ControlForm  # Use the custom form created for Control
    success_url = reverse_lazy('manage_controls')  # Redirect after successful edit

    def form_valid(self, form):
        # Get the control data from the form
        control = form.save(commit=False)  # Don't commit the save yet
        
        # Prepare the data you want to update
        updated_data = {
            'max_order_limit': form.cleaned_data.get('max_order_limit'),
            'max_loss_limit': form.cleaned_data.get('max_loss_limit'),
            'max_profit_limit': form.cleaned_data.get('max_profit_limit'),
            'max_profit_mode': form.cleaned_data.get('max_profit_mode'),
            'max_order_count_mode': form.cleaned_data.get('max_order_count_mode'),
            'is_killed_once': form.cleaned_data.get('is_killed_once'),
            'user': form.cleaned_data.get('user'),  # User field should be handled
        }
        
        # Update the fields in the Control model
        Control.objects.filter(pk=control.pk).update(**updated_data)

        # Add a success message and return the response
        messages.success(self.request, 'Control settings updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Print form errors to console for debugging
        print(form.errors)  # This will output any validation errors in the console
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_object(self, queryset=None):
        # Fetch the control object based on the URL parameter (control ID)
        return get_object_or_404(Control, pk=self.kwargs['pk'])  # Assuming you're using the control ID as a URL parameter


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import json

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

            

            if dhan_client_id:
                UserObj = User.objects.filter(dhan_client_id= dhan_client_id).first()
                dhan_access_token = UserObj.dhan_access_token
                print("dhan_access_tokendhan_access_token", dhan_access_token)
                dhan = dhanhq(dhan_client_id,dhan_access_token)
                orderlist = dhan.get_order_list()
                traded_order_count = get_traded_order_count_dhan(orderlist)  
                # fetch control data 
                control_data = Control.objects.filter(user=UserObj).first()
                print("control_datacontrol_datacontrol_data", control_data)
                print("traded_order_counttraded_order_count", traded_order_count)
                if control_data.max_order_count_mode:
                    if control_data.max_order_limit <=  traded_order_count:
                        # kill dhan
                        response = dhanKillProcess(dhan_access_token)
                        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^", response)
                        return JsonResponse({'status': 'success', 'message': 'Kill Activated successfully'})
                    else:
                        pass
            # Return a success response
            return JsonResponse({'status': 'success', 'message': 'Data received successfully'})
        
        except json.JSONDecodeError:
            # Handle JSON decoding errors
            logging.error("Invalid JSON received in postback")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        
    # If the request method is not POST, return a method not allowed error
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def get_traded_order_count_dhan(orderlist):
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^", orderlist)
    # Check if the response contains 'data'
    if 'data' not in response:
        return 0

    # Filter orders with 'orderStatus' as 'TRADED'
    traded_orders = [order for order in response['data'] if order.get('orderStatus') == 'TRADED']

    # Return the count of traded orders
    return len(traded_orders)



def dhanKillProcess(access_token):
    # Establish HTTPS connection to the Dhan API
    conn = http.client.HTTPSConnection("api.dhan.co")
    
    # Set up the payload (currently empty, modify if needed)
    payload = json.dumps({})
    
    # Define headers including the access-token
    headers = {
        'access-token': access_token,  # Add the access token here
        'Content-Type': "application/json",
        'Accept': "application/json"
    }
    
    try:
        # Make the POST request to the kill switch endpoint
        conn.request("POST", "/v2/killswitch", payload, headers)
        
        # Get the response
        res = conn.getresponse()
        data = res.read()
        
        # Decode the response and return as a Python dictionary
        response_data = data.decode("utf-8")
        return json.loads(response_data)
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    finally:
        # Close the connection
        conn.close()



def GetTotalOrderList(access_token):
    """
    Fetches the total list of orders from the Dhan API.

    Parameters:
    access_token (str): The access token for authenticating with the Dhan API.

    Returns:
    dict: Parsed JSON response from the API containing the list of orders.
    None: If there was an error during the request.
    """
    try:
        # Create a connection to the Dhan API
        conn = http.client.HTTPSConnection("api.dhan.co")

        # Set up headers including the access token
        headers = {
            'access-token': access_token,
            'Accept': "application/json"
        }

        # Make the request to get the orders
        conn.request("GET", "/v2/orders", headers=headers)

        # Get the response from the API
        res = conn.getresponse()
        data = res.read()

        # Decode the response and convert it into a Python dictionary
        order_data = json.loads(data.decode("utf-8"))

        # Return the parsed JSON data
        return order_data

    except Exception as e:
        # Handle any exceptions that may occur
        print(f"Error fetching order list: {e}")
        order_data = {}
        return order_data
