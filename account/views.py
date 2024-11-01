from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages, auth
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.http import JsonResponse
from datetime import datetime
import http.client
import json
import requests

from account.forms import UserLoginForm
from .forms import CustomUserCreationForm, UserForm, CustomControlCreationForm, ControlForm
from .models import Control

from dhanhq import dhanhq
from datetime import datetime, timedelta
# Get the custom user model
User = get_user_model()


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
                messages.success(request, f"Welcome back, {request.user.first_name}! You have successfully logged in.")
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
        # Save the form and add a success message
        response = super().form_valid(form)
        messages.success(self.request, "Registration successful! Please log in with your credentials.")
        return response

    def form_invalid(self, form):
        # Add an error message if the form is invalid
        messages.error(self.request, "There was an error with your registration. Please check the form and try again.")
        return super().form_invalid(form)



class ControlCreateView(CreateView):
    model = User
    form_class = CustomControlCreationForm
    template_name = "dashboard/create_control.html"  # Create this template for the control creation page
    success_url = reverse_lazy('login')  # Redirect to login page after successful control creation

    def form_valid(self, form):
        # Save the form and add a success message
        response = super().form_valid(form)
        messages.success(self.request, "Control created successfully! Please log in to manage it.")
        return response

    def form_invalid(self, form):
        # Add an error message if the form is invalid
        messages.error(self.request, "There was an error creating the control. Please check the form and try again.")
        return super().form_invalid(form)


@method_decorator(login_required(login_url='/'), name='dispatch')
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

        control_data = Control.objects.filter(user=user).first()

        total_realized_profit = 0.0

        # Fetch data from DHAN API using the user's credentials
        dhan = dhanhq(dhan_client_id, dhan_access_token)
        fund_data = dhan.get_fund_limits()
        orderlistdata = dhan.get_order_list()
        traded_orders = get_traded_order_filter_dhan(orderlistdata)
        order_count = get_traded_order_count(orderlistdata)
        total_expense = order_count * float(settings.BROKERAGE_PARAMETER)
        total_expense = float(total_expense)

        position_data = dhan.get_positions()
        current_date = datetime.now().date()
        position = []
        if 'data' not in position_data or not isinstance(position_data['data'], list) or not position_data['data']:
            positions = False
        else:
            positions = position_data['data']
        if positions:
            total_realized_profit = sum(position['realizedProfit'] for position in positions) if positions else 0.00
            total_realized_profit = float(total_realized_profit)

        # Sample static position data (this should ideally come from the API)
        position_data_json = json.dumps(position_data['data'])
        actual_profit = total_realized_profit - total_expense
        opening_balance = float(fund_data['data']['sodLimit'])
        available_balance = float(fund_data['data']['availabelBalance'])
        actual_balance = opening_balance + actual_profit
        if opening_balance >= available_balance:
            actual_bal = opening_balance
        else:
            actual_bal = available_balance

        if actual_profit and actual_bal:
            pnl_percentage = (actual_profit / actual_bal) * 100
        else:
            pnl_percentage = 0
        if control_data:
            order_limit = control_data.peak_order_limit
            stoploss_percentage = control_data.stoploss_percentage
        else:
            order_limit = 0
        day_exp_brokerge = float(order_limit) * float(settings.BROKERAGE_PARAMETER)
        exp_entry_count = order_limit // 2 
        actual_entry_count = order_count // 2 

        # data for chart - break up 
        breakup_series = [actual_balance, actual_profit, total_expense ]
        breakup_labels = ['A/C Balance', 'Profit/Loss', 'Charges']

        max_expected_loss = (actual_bal * exp_entry_count ) * (stoploss_percentage/100)
        max_expected_expense = float(max_expected_loss) + day_exp_brokerge



        # Market Quote Data                    
        index_data = dhan.ohlc_data(
            securities = {"NSE_EQ":[13]}
        )

        print("index_dataindex_data", index_data)




        # Add data to context
        context['breakup_series'] = breakup_series
        context['actual_entry_count'] = actual_entry_count
        context['exp_entry_count'] = exp_entry_count
        context['breakup_labels'] = breakup_labels
        context['max_expected_loss'] = max_expected_loss
        context['max_expected_expense'] = max_expected_expense
        context['fund_data'] = fund_data
        context['pnl_percentage'] = pnl_percentage
        context['day_exp_brokerge'] = day_exp_brokerge
        context['order_limit'] = order_limit
        context['user'] = user
        context['orderlistdata'] = traded_orders
        context['position_data'] = position_data
        context['current_date'] = current_date
        context['position_data_json'] = position_data_json
        context['total_realized_profit'] = total_realized_profit
        context['total_expense'] = total_expense
        context['order_count'] = order_count
        context['orderlistdata'] = orderlistdata
        context['actual_profit'] = actual_profit
        context['actual_balance'] = actual_balance

        # Add the slug to the context if needed
        context['slug'] = self.slug
        
        # Add the users to the context
        context['users'] = self.users
        context['dashboard_view'] = self.dashboard_view

        return context


def get_traded_order_count(order_list):
    
    # Check if 'data' key is in order_list and that 'data' is a list
    if 'data' not in order_list or not isinstance(order_list['data'], list) or not order_list['data']:
        return 0
    
    # Calculate traded_count if data list is not empty
    traded_count = len([order for order in order_list['data'] if order.get('orderStatus') == 'TRADED'])
    return traded_count if traded_count else 0

def get_traded_order_filter_dhan(response):
    # Check if 'data' key is in order_list and that 'data' is a list
    if 'data' not in response or not isinstance(response['data'], list) or not response['data']:
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




class UserListView(ListView):
    model = User  # This will now refer to the custom user model
    template_name = 'dashboard/user_list_view.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return User.objects.all()  # Optionally filter the users as per your requirements


def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    # Check if user has permission to delete (optional)
    if request.user.is_superuser and not user == request.user :
        user.delete()
        messages.success(request, "User deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this user.")
    return redirect('manage_user') 


def clear_kill_log(request):
    if request.user.is_authenticated:
        DhanKillProcessLog.objects.all().delete()
        messages.success(request, "All log data has been cleared successfully.")
    else:
        messages.error(request, "You need to be logged in to perform this action.")
    
    return redirect('dhan-kill-log-list')  # 

def check_log_status(request):
    # Get the username from the request
    username = request.GET.get('username')
    
    # Fetch the user and their DHAN credentials
    user = get_object_or_404(User, username=username)
    dhan_client_id = user.dhan_client_id
    dhan_access_token = user.dhan_access_token
    
    # Retrieve order count stored in session
    session_key = f"{username}_order_count"
    session_order_count = request.session.get(session_key, 0)
    
    # Fetch order count from DHAN API
    dhan = dhanhq(dhan_client_id, dhan_access_token)
    orderlistdata = dhan.get_order_list()
    actual_order_count = get_traded_order_count(orderlistdata)
    
    # Check if the order count has changed
    if session_order_count != actual_order_count:
        # Update session with new order count
        request.session[session_key] = actual_order_count
        # Respond with an indication to reload the page
        return JsonResponse({'status': 'reload'})
    
    # If no change, respond with a status indicating no reload is needed
    return JsonResponse({'status': 'no_change'})

# Manage Users: View and edit details of a specific user
class UserDetailView(UpdateView):
    model = User
    template_name = 'dashboard/user-detail-edit.html'  # Ensure this template exists
    context_object_name = 'user'
    form_class = UserForm  # Use the custom form created above
    success_url = reverse_lazy('manage_user')  # Redirect after successful edit

    def form_valid(self, form):
        # Get the user data from the form and prepare the data to update
        user = form.save(commit=False)  # Don't commit the save yet
        updated_data = {
            'email': form.cleaned_data.get('email'),
            'phone_number': form.cleaned_data.get('phone_number'),
            'role': form.cleaned_data.get('role'),
            'country': form.cleaned_data.get('country'),
            'dhan_access_token': form.cleaned_data.get('dhan_access_token'),
            'dhan_client_id': form.cleaned_data.get('dhan_client_id'),
            'status': form.cleaned_data.get('status'),
            'is_active': form.cleaned_data.get('is_active'),
            'kill_switch_1': form.cleaned_data.get('kill_switch_1'),
            'kill_switch_2': form.cleaned_data.get('kill_switch_2'),
            'quick_exit': form.cleaned_data.get('quick_exit'),
            
            # Add 'profile_image' if needed
        }
        # Update the user fields in the User model where username matches
        User.objects.filter(username=user.username).update(**updated_data)
        # Add a success message
        messages.success(self.request, 'User details updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Print form errors to console for debugging and add an error message
        print(form.errors)  # For debugging in the console
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_object(self, queryset=None):
        # Fetch the user object based on the URL parameter (user ID)
        return get_object_or_404(User, pk=self.kwargs['pk'])  # Assuming you're using the user ID as a URL parameter
        


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


from django.views.generic import ListView
from .models import DailyAccountOverview

class DailyAccountOverviewListView(ListView):
    model = DailyAccountOverview
    template_name = 'dashboard/dailyaccountoverview.html'  # Update template name as necessary
    context_object_name = 'daily_account_overviews'  # Change to reflect the context in the template
    paginate_by = 10  # Optional: Add pagination (adjust the number as needed)

    def get_queryset(self):
        # Return the queryset ordered by the updated_on field (descending)
        return DailyAccountOverview.objects.all().order_by('-updated_on')

    def get_context_data(self, **kwargs):
        # Add any additional context variables if needed
        context = super().get_context_data(**kwargs)
        context['title'] = 'Daily Account Overview'  # Optional: Add a title or other context variables
        return context

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
@require_POST
@csrf_exempt
def close_all_positions(request):
    data = json.loads(request.body)
    username = data.get('username')
    # Find the active user by username
    try:
        user = User.objects.get(is_active=True, username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found or inactive."}, status=404)
    
    # Initialize Dhan client
    dhan = dhanhq(user.dhan_client_id, user.dhan_access_token)
    order_list = dhan.get_order_list()

    # Check if the latest order entry matches criteria
    if order_list['data']:
        pending_sl_orders = get_pending_order_filter_dhan(order_list)
        print("pending_sl_orderspending_sl_orders", pending_sl_orders)
        if not pending_sl_orders == False :
            for orders in pending_sl_orders:
                cancel_slorder_response = dhan.cancel_order(order_id = orders['orderId'])  
                print("cancel_sl_order_response:", cancel_slorder_response)
        latest_buy_entry = get_latest_buy_order_dhan(order_list)
        print("------------------------------------------------latest buy entry:", latest_buy_entry)
        if latest_buy_entry:
            if latest_buy_entry['transactionType'] == 'BUY' and latest_buy_entry['orderStatus'] == 'TRADED':
                # Retrieve necessary details for the order
                sellorder_response = dhan.place_order(
                    security_id=latest_buy_entry['securityId'],
                    exchange_segment='NSE_FNO',
                    transaction_type='SELL',
                    quantity=latest_buy_entry['quantity'],
                    order_type='MARKET',
                    product_type='INTRADAY',
                    price=0
                )
                print("------------------------------------------------sellorder response:", sellorder_response)
                message = sellorder_response['remarks']['message'] if 'remarks' in sellorder_response and 'message' in sellorder_response['remarks'] else sellorder_response['remarks']['error_message']
                return JsonResponse({"message": message, "response": sellorder_response})
            else:
                return JsonResponse({"message": "No open BUY order to close."}, status=200)
        else:
            return JsonResponse({"message": "No orders found for the user {}".format(username)}, status=200)
    else:
        return JsonResponse({"message": "No orders found for the user {}".format(username)}, status=200)




def get_pending_order_filter_dhan(response): 
    # Check if the response contains 'data'
    if 'data' not in response:
        return False
    pending_sl_orders = [
        order for order in response['data']
        if order.get('orderStatus') == 'PENDING' and order.get('transactionType') == 'SELL'
    ]
    if not pending_sl_orders:
        return False  
    return pending_sl_orders


def get_latest_buy_order_dhan(response):
    # Check if the response contains 'data'
    if 'data' not in response:
        return 0
    # Filter to get only traded buy orders
    traded_buy_orders = [
        order for order in response['data']
        if order.get('orderStatus') == 'TRADED' and order.get('transactionType') == 'BUY'
    ]
    # Check if there are no traded buy orders
    if not traded_buy_orders:
        return False
    # Sort the buy orders by createTime in descending order to get the latest
    latest_buy_order = max(traded_buy_orders, key=lambda x: x['createTime'])

    return latest_buy_order

@login_required
@require_POST
@csrf_exempt
def activate_kill_switch(request):
    try:
        # Parse the JSON data from the request body
        data = json.loads(request.body)
        username = data.get('username')
        print("username:", username)
        
        # Fetch the user with the provided username
        user = User.objects.get(is_active=True, username=username)
        dhan_access_token = user.dhan_access_token

        url = 'https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE'
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'access-token': dhan_access_token}

        # Make the POST request to the external kill switch API
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            # traded_order_count = response.json().get("order_count", 0)  # Ensure 'traded_order_count' is defined
            # DhanKillProcessLog.objects.create(user=user, log=response.json(), order_count=traded_order_count)
            
            # Update user kill switch status
            if not user.kill_switch_1 and not user.kill_switch_2:
                user.kill_switch_1 = True
                message = f"Kill switch 1 activated for user: {username}"
            elif user.kill_switch_1 and not user.kill_switch_2:
                user.kill_switch_2 = True
                message = f"Kill switch 2 activated for user: {username}"
            else:
                message = f"Kill switch already fully activated for user: {username}"

            user.save()
            result = {"status": "success", "message": message}
        else:
            result = {"status": "error", "message": f"Failed to activate kill switch for user {username}: Status code {response.status_code}"}
    
    except User.DoesNotExist:
        result = {"status": "error", "message": f"User {username} not found or inactive."}
    except requests.RequestException as e:
        result = {"status": "error", "message": f"Error activating kill switch for user {username}: {e}"}
    except Exception as e:
        result = {"status": "error", "message": f"An unexpected error occurred: {e}"}
    
    return JsonResponse(result)

