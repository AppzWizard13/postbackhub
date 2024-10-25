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
import requests
from datetime import datetime



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
        # Fetch slug from the URL if present, or default to using request.user
        self.slug = kwargs.get('slug')
        self.users = User.objects.filter(is_active=True)  # Query the active users
        self.dashboard_view = True

        # Call the parent class's dispatch method
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Get the existing context
        context = super().get_context_data(**kwargs)

        # If slug is present, use it to fetch the user associated with that slug
        if self.slug:
            user = User.objects.filter(username=self.slug).first()  # Adjust filter based on your slug logic
        else:
            # Use request.user if no slug is provided
            user = self.request.user

        # Fetch dhan_client_id and dhan_access_token from the user
        dhan_client_id = user.dhan_client_id
        dhan_access_token = user.dhan_access_token

        # Fetch data from DHAN API using the user's credentials
        dhan = dhanhq(dhan_client_id, dhan_access_token)
        fund_data = dhan.get_fund_limits()
        orderlistdata = dhan.get_order_list()
        traded_orders = get_traded_order_filter_dhan(orderlistdata)
        order_count = get_traded_order_count(orderlistdata)
        total_expense = order_count * 37.33

        position_data = dhan.get_positions()
        current_date = datetime.now().date()
        positions = position_data['data']
        total_realized_profit = sum(position['realizedProfit'] for position in positions) if positions else 0.00

        # Sample static position data (this should ideally come from the API)
        position_data_json = json.dumps(position_data['data'])
        actual_profit = total_realized_profit - total_expense

        # Add data to context
        context['fund_data'] = fund_data
        context['orderlistdata'] = traded_orders
        context['position_data'] = position_data
        context['current_date'] = current_date
        context['position_data_json'] = position_data_json
        context['total_realized_profit'] = total_realized_profit
        context['total_expense'] = total_expense
        context['order_count'] = order_count
        context['orderlistdata'] = orderlistdata
        context['actual_profit'] = actual_profit


        

        # Add the slug to the context if needed
        context['slug'] = self.slug
        
        # Add the users to the context
        context['users'] = self.users
        context['dashboard_view'] = self.dashboard_view

        return context


def get_traded_order_count(order_list):
    if 'data' not in order_list:
        return 0
    return len([order for order in order_list['data'] if order.get('orderStatus') == 'TRADED'])

def get_traded_order_filter_dhan(response):
    # Check if the response contains 'data'
    if 'data' not in response:
        return 0

    # Filter orders with 'orderStatus' as 'TRADED'
    traded_orders = [order for order in response['data'] if order.get('orderStatus') == 'TRADED']

    # Return the count of traded orders
    return traded_orders


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
            'is_active': form.cleaned_data.get('is_active'),
            # 'profile_image': form.cleaned_data.get('profile_image'), # Include this if needed and make sure it's handled correctly
        }
        # Update the user fields in the User model where username matches
        User.objects.filter(username=user.username).update(**updated_data)
        # Add a success message and return the response
        messages.success(self.request, 'User details updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Print form errors to console for debugging
        print(form.errors)  # This will output any validation errors in the console
        # messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_object(self, queryset=None):
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
            'peak_order_limit': form.cleaned_data.get('peak_order_limit'),
            'max_loss_limit': form.cleaned_data.get('max_loss_limit'),
            'max_profit_limit': form.cleaned_data.get('max_profit_limit'),
            'max_profit_mode': form.cleaned_data.get('max_profit_mode'),
            'max_order_count_mode': form.cleaned_data.get('max_order_count_mode'),
            'stoploss_percentage': form.cleaned_data.get('stoploss_percentage'),
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


from django.views.generic import ListView
from .models import DhanKillProcessLog

class DhanKillProcessLogListView(ListView):
    model = DhanKillProcessLog
    template_name = 'dashboard/dhan_kill_process_log_list.html'  # Specify your template name
    context_object_name = 'logs'
    paginate_by = 10  # Optional: Add pagination (adjust the number as needed)

    def get_queryset(self):
        return DhanKillProcessLog.objects.all().order_by('-created_on')
