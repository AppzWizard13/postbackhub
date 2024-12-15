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
from datetime import date
import http.client
import json
import requests

from account.forms import UserLoginForm
from .forms import CustomUserCreationForm, UserForm, CustomControlCreationForm, ControlForm
from .models import Control
from django.views.generic import ListView
from .models import DhanKillProcessLog
from .models import DailyAccountOverview

from dhanhq import dhanhq
from datetime import datetime, timedelta
# Get the custom user model
User = get_user_model()


# Create your views here.
class HomePageView( TemplateView):
    template_name = "landing/index.html"


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
        if not self.request.user.is_superuser:
            messages.error(self.request, "You Have No Previllage to Add Membres. Please Contact Admin.")
            return super().form_invalid(form)
            
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
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        # Save the form and add a success message
        response = super().form_valid(form)
        messages.success(self.request, "Control created successfully! Please log in to manage it.")
        return response

    def form_invalid(self, form):
        # Add an error message if the form is invalid
        messages.error(self.request, "There was an error creating the control. Please check the form and try again.")
        return super().form_invalid(form)

import pytz
@method_decorator(login_required(login_url='/'), name='dispatch')
class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            # Fetch slug from the URL if present, or default to using request.user
            self.slug = kwargs.get('slug')
            self.users = User.objects.filter(is_active=True)  # Query the active users
            self.allusers = User.objects.filter(is_active=True)  # Query the active users
            self.dashboard_view = True

            # Call the parent class's dispatch method
            return super().dispatch(request, *args, **kwargs)

        except Exception as e:
            # Log the exception (optional, for debugging purposes)
            print(f"Error in DashboardView: {e}")
            # Redirect to '/users/' if any exception occurs
            return redirect('/users/')

    def get_context_data(self, **kwargs):
        # Get the existing context
        context = super().get_context_data(**kwargs)
        import pytz
        from datetime import datetime

        # Get the Asia/Kolkata timezone
        ist = pytz.timezone('Asia/Kolkata')

        # Get the current time in the specified timezone
        now = datetime.now(ist)

        # Get today's date
        today = now.date()

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
        holdings = dhan.get_holdings()
        orderlistdata = dhan.get_order_list()
        traded_orders = get_traded_order_filter_dhan(orderlistdata)
        pending_sl_order = get_pending_order_filter_dhan(orderlistdata)
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
        all_positions = position_data['data']
        open_position = [
            {'tradingSymbol': position['tradingSymbol'], 'securityId': position['securityId']}
            for position in all_positions
            if isinstance(position, dict) and position.get('positionType') != 'CLOSED'
        ]

        actual_profit = total_realized_profit - total_expense

        # Validate fund_data structure and types
        if (
            isinstance(fund_data, dict) and
            'data' in fund_data and
            isinstance(fund_data['data'], dict)
        ):
            # Extract and validate 'sodLimit'
            opening_balance = float(fund_data['data'].get('sodLimit', 0))  # Default to 0 if missing or invalid
            # Extract and validate 'availabelBalance'
            available_balance = float(fund_data['data'].get('availabelBalance', 0))  # Default to 0 if missing or invalid
        else:
            # Handle invalid fund_data structure
            opening_balance = 0.0
            available_balance = 0.0

        # Calculate actual balance
        actual_balance = opening_balance + actual_profit

        brokerage_only = 20
        if opening_balance >= available_balance:
            actual_bal = opening_balance
        else:
            actual_bal = available_balance

        if actual_profit and actual_bal:
            pnl_percentage = (actual_profit / actual_bal) * 100
        else:
            pnl_percentage = 0

        order_limit = 0
        if control_data:
            order_limit = control_data.max_order_limit
            peak_order_limit = control_data.peak_order_limit
            stoploss_parameter = control_data.stoploss_parameter
            stoploss_type = control_data.stoploss_type
        else:
            peak_order_limit = 0
            stoploss_type =""
        
        day_exp_brokerge = float(peak_order_limit) * float(settings.BROKERAGE_PARAMETER)



        exp_entry_count = peak_order_limit // 2 
        actual_entry_count = order_count // 2 
        remaining_trades = (peak_order_limit - order_count) // 2
        
        # data for chart - break up 
        if total_realized_profit > 0 :
            breakup_series = [opening_balance, total_realized_profit, total_expense ]
        elif total_realized_profit < 0 :
            breakup_series = [available_balance, total_realized_profit, total_expense ]
        else:
            breakup_series = [available_balance, total_realized_profit, total_expense ]

        
        breakup_labels = ['A/C Balance', 'Profit/Loss', 'Charges']
        max_expected_loss = 0 
        max_expected_expense = 0 
        
        if control_data:
            if control_data.stoploss_type ==  "price" :
                max_expected_loss = remaining_trades  * stoploss_parameter
                max_expected_expense = float(max_expected_loss) + day_exp_brokerge
            else:
                max_expected_loss = (actual_bal * remaining_trades ) * (stoploss_parameter/100)
                max_expected_expense = float(max_expected_loss) + day_exp_brokerge

        from django.db.models import F, Sum

        hourly_status_data = list(
            DailyAccountOverview.objects
            .filter(user=user)
            .annotate(total=F('closing_balance'))  # Compute total for each record
            .order_by('-updated_on')
            .values_list('total', flat=True)[:20]
        )[::-1]
        
        remaining_orders = peak_order_limit - order_count
        progress_percentage = ( remaining_orders / peak_order_limit) * 100
        # Determine the progress bar color
        if progress_percentage >= 60:
            progress_color = 'green'
        elif progress_percentage >= 40:
            progress_color = 'yellow'
        elif progress_percentage >= 20:
            progress_color = 'orange'
        else:
            progress_color = 'red'

        from django.db.models import Q
        import re

        # Fetch the existing analysis for the user
        existing_analysis = DailySelfAnalysis.objects.filter(
            user=user, 
            date_time__date=today
        ).first()

        # Log the raw overall_advice for debugging
        if existing_analysis:
            print("Raw overall_advice:", existing_analysis.overall_advice)

        # Process overall_advice to create a dictionary
        if existing_analysis and existing_analysis.overall_advice:
            # Remove parentheses and unnecessary spaces
            cleaned_advice = re.sub(r"[()]", "", existing_analysis.overall_advice)

            # Split the cleaned advice into individual pieces
            advice_items = cleaned_advice.split("', '")

            # Create a dictionary from the advice items
            advice_dict = {}
            for i in range(0, len(advice_items), 2):  # Iterate in pairs (advice, tip)
                if i + 1 < len(advice_items):
                    key = advice_items[i].strip().strip("'")
                    value = advice_items[i + 1].strip().strip("'")
                    advice_dict[key] = value
        else:
            # If no analysis or advice found, initialize an empty dictionary
            advice_dict = {}

        print("Processed advice_dict:", advice_dict)

        print("existing_analysisexisting_analysisexisting_analysis", advice_dict) 

        print("hourly_status_datahourly_status_data", hourly_status_data)

        from django.db.models import F

        # Fetch the data with a renamed annotation to avoid conflict with the existing model field
        data = list(
            DailyAccountOverview.objects
            .filter(user=user)
            .annotate(
                annotated_pnl_status=F('pnl_status')  # Rename annotation to avoid conflict with model field
            )
            .order_by('-updated_on')
            .values('annotated_pnl_status')[:20]
        )[::-1]  # Reverse the order to get the latest records first

        # Count how many annotated_pnl_status values are positive
        positive_pnl_count = sum(1 for entry in data if entry['annotated_pnl_status'] > 0)
        # Calculate the accuracy as a percentage
        total_entries = len(data)
        accuracy = (positive_pnl_count / total_entries) * 100 if total_entries > 0 else 0

        # Print or store the accuracy and count for further use
        print(f"Accuracy: {accuracy}%")
        print(f"Positive PnL count: {positive_pnl_count}")
        print(f"Total Entries: {total_entries}")

        charge_per_trade = 2 * float(settings.BROKERAGE_PARAMETER)
        max_reamining_expense = charge_per_trade * (remaining_orders // 2 )
        print("max_reamining_expensemax_reamining_expense", max_reamining_expense)
        print("available_balanceavailable_balanceavailable_balance", available_balance)
        print("max_reamining_expensemax_reamining_expense", max_reamining_expense)
        if stoploss_type == 'price' and remaining_orders > 0 :
            forecast_balance = available_balance - stoploss_parameter - charge_per_trade
            day_risk_forecast = available_balance - (stoploss_parameter * remaining_trades ) - max_reamining_expense

        else :
            forecast_balance = "0.00"
            day_risk_forecast = available_balance - max_reamining_expense

        from django.core.exceptions import ObjectDoesNotExist

        # Assuming 'user' and 'today' are already defined
        try:
            daily_goal_data = DailyGoalReport.objects.filter(user=user, date=today).get()
            print("Daily Goal Data:", daily_goal_data)
        except DailyGoalReport.DoesNotExist:
            print(f"No daily goal found for user {user} on {today}")
            # You can assign a default value or handle accordingly
            daily_goal_data = None  # or create a new entry if needed



        try:
            used_rtc = UserRTCUsage.objects.get(user=user)
            used_rt_count = int(used_rtc.usage_count)
        except UserRTCUsage.DoesNotExist:
            # Handle case where no data is found
            used_rt_count = 0  # or any default value

        weekly_trade_count = int((int(control_data.default_peak_order_limit) / 2 * 5) + int(user.reserved_trade_count) + used_rt_count)
        start_date, end_date = get_current_week_start_and_end_dates()

        # You can also directly set start_date and end_date like this if needed:
        # start_date = '2024-11-10'  # Example date, adjust as necessary   

        print("weekly_trade_count:", weekly_trade_count)

        # Query to filter records within the date range
        results = DailyAccountOverview.objects.filter(user=user,day_open=False,
            updated_on__date__range=(start_date, end_date)
        ).order_by('id')  # Order by id

        # Add serial number to each result
        weekly_data = list(results.values('id', 'actual_profit', 'updated_on'))

        # Add serial number manually in Python
        for index, entry in enumerate(weekly_data, start=1):
            entry['serial_number'] = index

        # Optional: Calculate total profit for the week
        weekly_total_profit = results.aggregate(Sum('actual_profit'))['actual_profit__sum']

        print("weekly_data:", weekly_data)
        print("Total Profit:", weekly_total_profit)

        # Create weekly_progress_data with length equal to weekly_trade_count
        weekly_progress_data = []
        available_serial_numbers = {trade_data['serial_number']: trade_data for trade_data in weekly_data}

        # Iterate over serial numbers from 1 to weekly_trade_count
        for i in range(1, weekly_trade_count + 1):
            if i in available_serial_numbers:
                weekly_progress_data.append(available_serial_numbers[i])  # Add the trade data for matching serial number
            else:
                # If no data exists for this serial number, add a placeholder
                weekly_progress_data.append({'serial_number': i, 'status': 'No trade'})

        # At this point, weekly_progress_data will have the same length as weekly_trade_count
        print("Weekly Progress Data:", weekly_progress_data)
                
         

        context['accuracy'] = accuracy
        context['weekly_progress_data'] = weekly_progress_data
        context['weekly_trade_count'] = range(weekly_trade_count)
        context['progress_color'] = progress_color
        context['open_position'] = open_position
        context['pending_sl_order'] = pending_sl_order
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
        context['peak_order_limit'] = peak_order_limit
        context['user'] = user
        context['advice_dict'] = advice_dict
        context['stoploss_parameter'] = stoploss_parameter
        context['stoploss_type'] = stoploss_type[:7].upper()
        context['hourly_status_data'] = hourly_status_data
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
        context['daily_goal_data'] = daily_goal_data
        # context['weekly_goal_data'] = weekly_goal_data
        context['remaining_orders'] = remaining_orders
        context['remaining_trades'] = remaining_orders // 2 
        context['progress_percentage'] = progress_percentage
        context['forecast_balance'] = forecast_balance
        context['available_balance'] = available_balance
        context['day_risk_forecast'] = day_risk_forecast




        # Add the slug to the context if needed
        context['slug'] = self.slug
        
        # Add the users to the context
        context['users'] = self.users
        context['allusers'] = self.allusers
        context['dashboard_view'] = self.dashboard_view

        return context

def get_current_week_start_and_end_dates():
    today = datetime.today()
    # Calculate the start of the week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    # Calculate the end of the week (Friday)
    end_of_week = start_of_week + timedelta(days=4)
    return start_of_week.date(), end_of_week.date()

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

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

def check_log_status(request):
    # Get the username from the request
    username = request.GET.get('username')
    
    # Fetch the user and their DHAN credentials
    user = get_object_or_404(User, username=username)
    dhan_client_id = user.dhan_client_id
    dhan_access_token = user.dhan_access_token
    
    # Retrieve kill switch values and order count from the session
    kill_switch_key = f"{username}_kill_switch"
    session_kill_switch = request.session.get(kill_switch_key, {"kill_switch_1": None, "kill_switch_2": None})
    session_order_count_key = f"{username}_order_count"
    session_order_count = request.session.get(session_order_count_key, 0)
    
    # Fetch current kill switch values
    current_kill_switch = {"kill_switch_1": user.kill_switch_1, "kill_switch_2": user.kill_switch_2}
    
    # Fetch order count from DHAN API
    dhan = dhanhq(dhan_client_id, dhan_access_token)
    orderlistdata = dhan.get_order_list()
    actual_order_count = get_traded_order_count(orderlistdata)
    
    # Check if there are changes in order count or kill switch values
    if (session_order_count != actual_order_count) or (session_kill_switch != current_kill_switch):
        # Update session with new values
        request.session[session_order_count_key] = actual_order_count
        request.session[kill_switch_key] = current_kill_switch
        # Respond with an indication to reload the page
        return JsonResponse({'status': 'reload'})
    
    # If no changes, respond with a status indicating no reload is needed
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
        if self.request.user.is_superuser:
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
                'sl_control_mode': form.cleaned_data.get('sl_control_mode')
                # Add 'profile_image' if needed
            }
            # Update the user fields in the User model where username matches
            User.objects.filter(username=user.username).update(**updated_data)
            # Add a success message
            messages.success(self.request, 'User details updated successfully.')
        else:
            messages.error(self.request, 'You have No previllage to Edit User Settings.')
            return super().form_invalid(form)

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
        if self.request.user.is_superuser:
            control = form.save(commit=False)  # Don't commit the save yet
            
            # Prepare the data you want to update
            updated_data = {
                'max_order_limit': form.cleaned_data.get('max_order_limit'),
                'peak_order_limit': form.cleaned_data.get('peak_order_limit'),
                'max_loss_limit': form.cleaned_data.get('max_loss_limit'),
                'peak_loss_limit': form.cleaned_data.get('peak_loss_limit'),
                'max_profit_limit': form.cleaned_data.get('max_profit_limit'),
                'max_profit_mode': form.cleaned_data.get('max_profit_mode'),
                'max_order_count_mode': form.cleaned_data.get('max_order_count_mode'),
                'stoploss_parameter': form.cleaned_data.get('stoploss_parameter'),
                'user': form.cleaned_data.get('user'),  # User field should be handled
            }
            
            # Update the fields in the Control model
            Control.objects.filter(pk=control.pk).update(**updated_data)

            # Add a success message and return the response
            messages.success(self.request, 'Control settings updated successfully.')
        else:
            messages.error(self.request, 'You have No previllage to Edit Controls.')
            return super().form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        # Print form errors to console for debugging
        print(form.errors)  # This will output any validation errors in the console
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_object(self, queryset=None):
        # Fetch the control object based on the URL parameter (control ID)
        return get_object_or_404(Control, pk=self.kwargs['pk'])  # Assuming you're using the control ID as a URL parameter




class DhanKillProcessLogListView(ListView):
    model = DhanKillProcessLog
    template_name = 'dashboard/dhan_kill_process_log_list.html'  # Specify your template name
    context_object_name = 'logs'
    paginate_by = 10  # Optional: Add pagination (adjust the number as needed)

    def get_queryset(self):
        return DhanKillProcessLog.objects.all().order_by('-created_on')


from django.utils.dateparse import parse_date
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

class DailyAccountOverviewListView(ListView):
    model = DailyAccountOverview
    template_name = 'dashboard/dailyaccountoverview.html'
    context_object_name = 'daily_account_overviews'
    paginate_by = 20

    def get_queryset(self):
        queryset = DailyAccountOverview.objects.all().order_by('-updated_on')

        # Filter by user if a user_id is provided in the GET parameters
        user_id = self.request.GET.get('user_id')
        if user_id:
            queryset = queryset.filter(user__id=user_id)

        # Filter by date range if start_date and end_date are provided in the GET parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            start_date_parsed = parse_date(start_date)
            if start_date_parsed:
                queryset = queryset.filter(updated_on__date__gte=start_date_parsed)
        if end_date:
            end_date_parsed = parse_date(end_date)
            if end_date_parsed:
                queryset = queryset.filter(updated_on__date__lte=end_date_parsed)

        # Filter by opening and closing status if provided in the GET parameters
        day_open = self.request.GET.get('day_open')
        day_close = self.request.GET.get('day_close')
        if day_open is not None:
            queryset = queryset.filter(day_open=(day_open.lower() == 'true'))
        if day_close is not None:
            queryset = queryset.filter(day_close=(day_close.lower() == 'true'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Daily Account Overview'

        # Add filters to the context for form binding in the template
        context['user_list'] = User.objects.all()
        context['selected_user'] = self.request.GET.get('user_id', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['day_open'] = self.request.GET.get('day_open', '')
        context['day_close'] = self.request.GET.get('day_close', '')

        return context


from django.db.models import Q
from .models import  OrderHistoryLog

class orderHistoryListView(ListView):
    model = OrderHistoryLog
    template_name = 'dashboard/order_history_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        # Filter by user if a user_id is provided in the GET parameters
        user_id = self.request.GET.get('user_id')
        if user_id:
            self.user = User.objects.filter(id=user_id).first()  # Store user as instance attribute
        else:
            self.user = self.request.user

        # Get the selected date from the GET parameters
        selected_date = self.request.GET.get('date')
        selected_date_parsed = parse_date(selected_date) if selected_date else None
        current_date = date.today()

        # If no date is provided or if the selected date is the current date, fetch data from the Dhan API
        if selected_date_parsed is None or selected_date_parsed == current_date:
            # Get Dhan client data
            dhan = dhanhq(self.user.dhan_client_id, self.user.dhan_access_token)
            # Fetch order list data from Dhan API
            order_list = dhan.get_order_list()

            # You can return the data from the Dhan API if needed for the view, or store it in context
            self.orderlistdata = order_list

            # Since we're fetching from Dhan API, we don't need to filter by the DB table
            return OrderHistoryLog.objects.none()  # No data from DB needed for today

        else:
            # If the selected date is in the past, fetch from the OrderHistoryLog table
            queryset = OrderHistoryLog.objects.all()

            if selected_date_parsed:
                queryset = queryset.filter(date=selected_date_parsed)

            # Add any additional filtering conditions here if necessary

            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Include the full list of users to display in the context
        context['user_list'] = User.objects.all()

        # Optionally, you can pass the filtered order list data from the API here (for current date)
        if hasattr(self, 'orderlistdata'):
            context['orderlistdata'] = self.orderlistdata

        # Pass the user object to the context
        context['user'] = self.user  # Use self.user, which is set in get_queryset()

        # Pass today's date to the template context
        context['today'] = date.today()

        return context



from django.views.generic import TemplateView
from datetime import datetime, date
from django.utils.dateparse import parse_date

class TradeHistoryListView(TemplateView):
    template_name = 'dashboard/trade_history_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user info
        user_id = self.request.GET.get('user_id')
        if user_id:
            self.user = User.objects.filter(id=user_id).first()
        else:
            self.user = self.request.user

        # Get start and end dates from GET parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # Parse and validate the dates
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None

        current_date = date.today()
        if not start_date_parsed:
            start_date_parsed = current_date
        if not end_date_parsed:
            end_date_parsed = current_date

        # Ensure start_date <= end_date
        if start_date_parsed > end_date_parsed:
            end_date_parsed = start_date_parsed

        # Format dates as strings for the API call
        from_date_str = start_date_parsed.strftime('%Y-%m-%d')
        to_date_str = end_date_parsed.strftime('%Y-%m-%d')


        # Fetch trade history from Dhan API
        dhan = dhanhq(self.user.dhan_client_id, self.user.dhan_access_token)
        response = dhan.get_trade_history(from_date_str, to_date_str, page_number=0)
        trade_history = response['data']

        # Initialize total charges sum
        total_charges = 0

        # Add 'charges' field for each log and calculate total charges
        for trade in trade_history:
            charges = sum([
                trade.get('sebiTax', 0),
                trade.get('stt', 0),
                trade.get('brokerageCharges', 0),
                trade.get('serviceTax', 0),
                trade.get('exchangeTransactionCharges', 0),
                trade.get('stampDuty', 0)
            ])
            trade['charges'] = charges
            total_charges += charges  # Add to total charges

        # Calculate total order counts
        total_order_counts = len(trade_history)  # Total number of orders

        # Add trade history data, total charges, and total order counts to the context
        context['user_list'] = User.objects.all()
        context['trade_history'] = trade_history
        context['selected_start_date'] = start_date_parsed
        context['selected_end_date'] = end_date_parsed
        context['total_charges'] = total_charges  # Pass total charges to context
        context['total_order_counts'] = total_order_counts  # Pass total order counts to context

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
    # Check if the response contains 'data' and if it's a list
    if 'data' not in response or not isinstance(response['data'], list):
        return False
    
    pending_sl_orders = [
        order for order in response['data']
        if isinstance(order, dict) and
           order.get('orderStatus') == 'PENDING' and
           order.get('transactionType') == 'SELL'
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
                user.status = False
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

from django.shortcuts import render, redirect
from .forms import DailySelfAnalysisForm
from django.contrib import messages
import random


# Revised ADVICE_POOL with Professional Trading Concepts and Core Psychology

ADVICE_POOL = {
    "health_check": {
        "0-20": [
            ("Physical condition is low, which can negatively impact decision-making and emotional control.",
             "Tip: Avoid trading until your physical state improves. Focus on recovery activities like rest, hydration, and nutrition. A fatigued body leads to impaired cognitive performance."),
        ],
        "21-40": [
            ("Your energy levels are below optimal. Avoid making major decisions or handling complex trades.",
             "Tip: Engage in mindfulness or relaxation techniques to reset and recharge. Trading when physically drained can lead to overtrading or poor decision-making."),
        ],
        "41-60": [
            ("Your energy is moderate. You may experience periods of fatigue, affecting concentration and emotional regulation.",
             "Tip: Incorporate short breaks and maintain consistent hydration to keep your energy stable. Avoid emotional decision-making and stick to a strategy."),
        ],
        "61-80": [
            ("Good physical state, allowing you to handle stressful situations with composure.",
             "Tip: Leverage your energy levels to stay focused and keep your risk management strategies in place. Remain alert, especially during high-volatility periods."),
        ],
        "81-100": [
            ("Peak physical condition. You’re prepared to make high-stakes, strategic trades.",
             "Tip: Use this energy wisely, maintaining a disciplined approach to trading. Avoid impulsive trades and focus on your long-term strategy and risk tolerance."),
        ],
    },
    "mind_check": {
        "0-20": [
            ("Your mental clarity is significantly low, which can impair your ability to analyze data and make rational decisions.",
             "Tip: Take time off from the markets. Engage in activities like meditation, light exercise, or a short walk to reset your mental state."),
        ],
        "21-40": [
            ("Mental clarity is suboptimal. Avoid making any major trading decisions as it may lead to mistakes.",
             "Tip: Use relaxation techniques to calm your mind. Mental fatigue can lead to emotional overreaction and a loss of focus."),
        ],
        "41-60": [
            ("Your mental state is steady, though you may encounter moments of distraction or emotional bias.",
             "Tip: Stay grounded with mindfulness practices, and always follow your pre-established trading plan to avoid letting emotions drive decisions."),
        ],
        "61-80": [
            ("Your mind is sharp and focused. You’re ready to assess market data effectively and execute trades with precision.",
             "Tip: Use this clarity to identify market trends, but stay cautious. Overconfidence can lead to risk-taking behaviors that deviate from your strategy."),
        ],
        "81-100": [
            ("You’re in an optimal mental state, able to think critically and analytically under pressure.",
             "Tip: Maintain discipline and stick to your risk management plan. You are capable of handling complex strategies and unpredictable market shifts."),
        ],
    },
    "expectation_level": {
        "0-20": [
            ("Expectations are too low. Avoid trading if you’re feeling defeated or discouraged.",
             "Tip: Focus on building your confidence with smaller, risk-managed trades or consider reviewing educational content before re-engaging."),
        ],
        "21-40": [
            ("Expectations are cautious but grounded. You are preparing for moderate trades that match your current mindset.",
             "Tip: Ensure that your trades align with your current market outlook. Don’t rush decisions based on a fear of missing out (FOMO)."),
        ],
        "41-60": [
            ("Expectations are balanced. You are in a state to trade with a calm and calculated mindset.",
             "Tip: Trust your process and remain patient. Avoid chasing the market; let your strategy come to you."),
        ],
        "61-80": [
            ("Expectations are high. Use this confidence to execute your strategy effectively, but don’t become overconfident.",
             "Tip: Don’t ignore risk management, and stay disciplined in your decision-making. Avoid emotional reactions if trades don’t go your way."),
        ],
        "81-100": [
            ("Your expectations are very high. It’s important to manage this enthusiasm by keeping an eye on market risk and uncertainty.",
             "Tip: While confidence can be an asset, overconfidence can lead to reckless behavior. Stay grounded and use data to drive your decisions."),
        ],
    },
    "patience_level": {
        "0-20": [
            ("Patience is low, which could result in impulsive decisions and overtrading.",
             "Tip: Step away from the markets to reset. Impulsive trades often result in poor outcomes. Revisit your strategy after a short break."),
        ],
        "21-40": [
            ("Patience is below average. You may feel the urge to enter trades too early or take profits prematurely.",
             "Tip: Practice mindfulness or deep breathing before making trades. Use alerts and automated orders to manage impatience."),
        ],
        "41-60": [
            ("You have moderate patience. Resist the urge to act on every market movement. Good patience allows you to wait for favorable setups.",
             "Tip: Stick to your strategy and avoid chasing the market. Slow and steady wins the race."),
        ],
        "61-80": [
            ("Patience is good. You are able to wait for the right setups and take a more measured approach to risk.",
             "Tip: Continue exercising patience, and be ready to capitalize on opportunities when they align with your plan."),
        ],
        "81-100": [
            ("Patience is at its peak. You are in the optimal state for waiting for high-confidence, low-risk trades.",
             "Tip: Use this patience to stay disciplined even during periods of market volatility. Execute your trades with precision."),
        ],
    },
    "previous_day_self_analysis": {
        "0-20": [
            ("Your reflection on yesterday’s trades shows a lack of awareness or understanding of your mistakes.",
             "Tip: Take time to review the lessons from your past trades. Learning from mistakes is crucial for improving your trading psychology."),
        ],
        "21-40": [
            ("You have some awareness of past errors but may not fully understand their root causes.",
             "Tip: Focus on improving your self-awareness and identifying specific areas where your trading plan went off track."),
        ],
        "41-60": [
            ("Your analysis of the previous day’s trades is balanced, with recognition of both strengths and weaknesses.",
             "Tip: Incorporate the insights from yesterday into your strategy today. Self-reflection is vital for growth in trading."),
        ],
        "61-80": [
            ("You’ve successfully identified key areas for improvement and strengths from your previous trades.",
             "Tip: Use these insights to refine your strategy and make informed decisions going forward."),
        ],
        "81-100": [
            ("Your self-analysis is sharp and constructive. You’ve used your past experiences to fine-tune your approach.",
             "Tip: Keep a trading journal to document your learnings and review regularly. This will continuously strengthen your approach."),
        ],
    },
    "overall": {
        "0-20": [ (
            "It may not be a good day to trade. Prioritize improving your mental and physical state before re-engaging in the markets.",
            "Tip: Take a break from trading and focus on self-care. A clear mind and good health are essential for making sound decisions in the markets."
        )],
        "21-40": [ (
            "Today calls for a cautious approach. Focus on lower-risk strategies and avoid the temptation to engage in high-stakes trading.",
            "Tip: Stick to a conservative strategy and avoid impulsive decisions. It's important to prioritize safety over aggressive trading."
        )],
        "41-60": [ (
            "You’re in a reasonable state for trading today. Stick to a well-structured plan and remain disciplined throughout.",
            "Tip: Trust your strategy and maintain discipline. Avoid reacting emotionally to market fluctuations."
        )],
        "61-80": [ (
            "You’re in a good place to trade with a balanced mindset and solid strategy. Keep emotions in check and focus on your risk management.",
            "Tip: Stay mindful of your emotions and stick to your risk management rules. It’s crucial to keep your trading consistent."
        )],
        "81-100": [ (
            "You’re in an optimal state to take on the markets. Execute your trades confidently but stay disciplined and mindful of risks.",
            "Tip: Take advantage of your optimal state by executing trades with confidence, but remember to stay disciplined and manage your risk."
        )]
    }

}

def get_advice(score, category):
    """Generate advice and tips based on score intervals for each category."""
    if score <= 20:
        advice = random.choice(ADVICE_POOL[category]["0-20"])
    elif 21 <= score <= 40:
        advice = random.choice(ADVICE_POOL[category]["21-40"])
    elif 41 <= score <= 60:
        advice = random.choice(ADVICE_POOL[category]["41-60"])
    elif 61 <= score <= 80:
        advice = random.choice(ADVICE_POOL[category]["61-80"])
    else:
        advice = random.choice(ADVICE_POOL[category]["81-100"])
    return advice

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.timezone import now
from . models import DailySelfAnalysis

def daily_self_analysis_view(request):
    if request.method == 'POST':
        form = DailySelfAnalysisForm(request.POST)
        if form.is_valid():
            # Check if a record already exists for today
            today = now().date()  # Get the current date
            existing_analysis = DailySelfAnalysis.objects.filter(
                user=request.user, 
                date_time__date=today
            ).first()  # Filter by user and date (date portion of date_time field)

            if existing_analysis:
                messages.error(request, "You have already submitted your self-analysis for today.")
                return redirect('daily_self_analysis')

            # Associate the logged-in user with the form before saving
            analysis = form.save(commit=False)
            analysis.user = request.user  # Set the logged-in user as the user for this analysis

            # Retrieve scores
            health_score = analysis.health_check
            mind_score = analysis.mind_check
            expectation_score = analysis.expectation_level
            patience_score = analysis.patience_level
            previous_day_score = analysis.previous_day_self_analysis

            # Calculate overall score
            overall_score = (health_score + mind_score + expectation_score + patience_score + previous_day_score) // 5

            # Generate advice and tips based on the scores
            advice_health = get_advice(health_score, "health_check")
            advice_mind = get_advice(mind_score, "mind_check")
            advice_expectation = get_advice(expectation_score, "expectation_level")
            advice_patience = get_advice(patience_score, "patience_level")
            advice_prev_day = get_advice(previous_day_score, "previous_day_self_analysis")
            advice_overall = get_advice(overall_score, "overall")

            # Compile advice into a list
            advice_list = [advice_health, advice_mind, advice_expectation, advice_patience, advice_prev_day, advice_overall]

            request.session['advice_list'] = advice_list

            # Save advice_list as a string in the overall_advice field
            analysis.overall_advice = ', '.join(str(advice) for advice in advice_list)


            # Save the analysis instance
            analysis.save()

            # Display success message
            messages.success(request, "Your self-analysis was submitted successfully.")

            # Redirect to the same page to avoid resubmission on refresh
            return redirect('daily_self_analysis')
        else:
            messages.error(request, "There was an error with your submission.")
    else:
        form = DailySelfAnalysisForm()
        # Retrieve advice list from session if it exists
        advice_list = request.session.pop('advice_list', None)

    return render(request, 'dashboard/daily_selfanalysis.html', {'form': form, 'advice_list': advice_list})

from .models import UserRTCUsage
import json

@login_required
@require_POST
@csrf_exempt
def use_rtc_action(request):
    try:
        # Parse the JSON data from the request body
        data = json.loads(request.body)
        username = data.get('username')

        # Fetch the user with the provided username
        user = User.objects.get(is_active=True, username=username)

        # Check if reserved_trade_count is 0
        if user.reserved_trade_count == 0:
            return JsonResponse({
                "status": "error",
                "message": "Your RTC is used completely. Wait till next week's starting."
            }, status=400)

        # Fetch the Control data for the user
        control_data = Control.objects.filter(user=user).first()
        if not control_data:
            return JsonResponse({
                "status": "error",
                "message": f"No control data found for user {username}."
            }, status=400)

        # Get or create a UserRTCUsage record for today
        today_usage, created = UserRTCUsage.objects.get_or_create(user=user, date=date.today())

        # Check if the user has already used RTC twice today
        if today_usage.usage_count >= 2:
            return JsonResponse({
                "status": "error",
                "message": "You have already used RTC twice today. Please wait until tomorrow."
            }, status=400)

        # Update peak_order_limit
        control_data.peak_order_limit += 2
        control_data.save()

        # Reduce reserved_trade_count
        user.reserved_trade_count -= 1
        user.save()

        # Increment the RTC usage count for today
        today_usage.usage_count += 1
        today_usage.save()

        # Return success message
        return JsonResponse({
            "status": "success",
            "message": f"Peak order limit updated to {control_data.peak_order_limit}. Reserved trade count reduced to {user.reserved_trade_count}. RTC used {today_usage.usage_count} times today."
        })

    except User.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"User {username} not found or inactive."
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)



# from django.shortcuts import redirect
# from django.contrib import messages
# from django.views.generic.edit import CreateView
# from django.urls import reverse_lazy
# from .forms import TradingPlanForm
# from .models import TradingPlan

# class CreateTradePlanView(CreateView):
#     model = TradingPlan
#     form_class = TradingPlanForm
#     template_name = "dashboard/trade_planner.html"  # The form view template

#     def form_valid(self, form):
#         # Save the form data and associate the user with the trading plan
#         trading_plan = form.save(commit=False)
#         trading_plan.user = self.request.user  # Assuming the user is logged in
#         trading_plan.save()

#         # Add a success message
#         messages.success(self.request, "Trade plan created successfully!")
#         return super().form_valid(form)

#     def form_invalid(self, form):
#         # Print the error details to the console
#         print("Error creating trade plan:", form.errors)

#         # Add an error message if the form is invalid
#         messages.error(self.request, form.errors)
#         return super().form_invalid(form)


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import WeeklyGoalReport, DailyGoalReport

@csrf_exempt
def save_goal_reports(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            weekly_data = data.get("weekly_data", [])
            daily_data = data.get("daily_data", [])

            # Save weekly data
            for week in weekly_data:
                week_report = WeeklyGoalReport.objects.create(
                    user=request.user,
                    plan_name=week['plan_name'],
                    week_number=week['week_number'],
                    accumulated_capital=week['accumulated_capital'],
                    gained_amount=week['gained_amount'],
                    progress=week['progress'],
                    is_achieved=week['is_achieved']
                )

                # Save daily data related to the weekly report
                for daily in daily_data:
                    if daily['plan_name'] == week['plan_name']:  # Match the plan_name
                        DailyGoalReport.objects.create(
                            user=request.user,
                            weekly_goal=week_report,
                            plan_name=daily['plan_name'],
                            day_number=daily['day_number'],
                            date=daily['date'],
                            capital=daily['capital'],
                            gained_amount=daily['gained_amount'],
                            is_achieved=daily['is_achieved'],
                            progress=daily['progress']
                        )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})



from django.http import JsonResponse
from django.shortcuts import render
from .forms import TradingPlanForm
from .models import TradingPlan  # Make sure this model is correctly imported

def create_trade_plan(request):
    if request.method == 'POST':
        form = TradingPlanForm(request.POST)
        
        if form.is_valid():
            plan_name = form.cleaned_data['plan_name']  # Get the plan name from the cleaned data
            
            # Check if the plan name already exists
            if TradingPlan.objects.filter(plan_name=plan_name).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': f'Trading plan with the name "{plan_name}" already exists.'
                })

            try:
                # Save the trade plan and associate it with the logged-in user
                trade_plan = form.save(commit=False)
                trade_plan.user = request.user
                trade_plan.save()

                # Return success response
                return JsonResponse({
                    'status': 'success',
                    'message': 'Trade plan saved successfully!'
                })
            except Exception as e:
                # Log the exception if needed
                print(f"Error saving trade plan: {e}")
                # Return the error response
                return JsonResponse({
                    'status': 'error',
                    'message': f'There was an error saving the trade plan: {e}'
                })
        else:
            # Convert form errors into plain text (removing HTML tags)
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)  # Add error message as plain text
            # If form is invalid, return form errors
            print("form.errorsform.errorsform.errors", form.errors)
            return JsonResponse({
                    'status': 'error',
                    'message': error_messages
                })

    else:
        # If the method is GET, just return the empty form
        form = TradingPlanForm()
        return render(request, 'dashboard/trade_planner.html', {'form': form})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import WeeklyGoalReport, DailyGoalReport
from django.contrib.auth.decorators import login_required

@csrf_exempt
@login_required
def save_goal_reports(request):
    if request.method == "POST":
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            weekly_data = data.get("weekly_data", [])
            daily_data = data.get("daily_data", [])
            
            # Save weekly reports
            for week in weekly_data:
                weekly_report, created = WeeklyGoalReport.objects.update_or_create(
                    user=request.user,
                    week_number=week["week_number"],
                    plan_name=week["plan_name"],
                    defaults={
                        "start_date": week["start_date"],
                        "end_date": week["end_date"],
                        "accumulated_capital": week["accumulated_capital"],
                        "gained_amount": week["gained_amount"],
                        "progress": week.get("progress", None),
                        "is_achieved": week.get("is_achieved", False),
                    },
                )

            # Save daily reports
            for day in daily_data:
                weekly_goal = WeeklyGoalReport.objects.get(
                    user=request.user,
                    week_number=day["week_number"],
                    plan_name=day["plan_name"]
                )
                DailyGoalReport.objects.update_or_create(
                    user=request.user,
                    weekly_goal=weekly_goal,
                    day_number=day["day_number"],
                    date=day["date"],
                    plan_name=day["plan_name"],
                    defaults={
                        "capital": day["capital"],
                        "gained_amount": day.get("gained_amount", None),
                        "is_achieved": day.get("is_achieved", False),
                        "progress": day.get("progress", None),
                    },
                )

            return JsonResponse({"success": True, "message": "Reports saved successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error saving reports: {e}"}, status=400)

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)


def trade_plan_list_view(request):
    """
    View to display the list of trading plans.
    """
    trading_plans = TradingPlan.objects.all()  # Fetch all trading plans
    context = {
        'trading_plans': trading_plans
    }
    return render(request, 'dashboard/trade_plan_listview.html', context)

from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from .models import TradingPlan, WeeklyGoalReport, DailyGoalReport
from datetime import timedelta
from decimal import Decimal


def generate_trading_plan(request, plan_id):
    # Fetch the trading plan
    trading_plan = get_object_or_404(TradingPlan, id=plan_id)

    # Retrieve plan data
    user = trading_plan.user
    initial_capital = Decimal(trading_plan.initial_capital)  # Ensure Decimal
    average_weekly_gain = Decimal(trading_plan.average_weekly_gain)  # Ensure Decimal
    no_of_weeks = trading_plan.no_of_weeks
    start_date = trading_plan.start_date

    # Clear existing reports for the plan to avoid duplication
    WeeklyGoalReport.objects.filter(user=user, plan_id=plan_id).delete()

    weeks_growth_rate = Decimal(1 + (average_weekly_gain / 100))
    accumulated_capital = initial_capital
    current_date = start_date

    for week_number in range(1, no_of_weeks + 1):
        # Calculate week start and end dates
        while current_date.weekday() != 0:  # Ensure it starts on Monday
            current_date += timedelta(days=1)
        monday_date = current_date
        friday_date = monday_date + timedelta(days=4)

        # Weekly calculations
        weekly_gain = (accumulated_capital * (weeks_growth_rate - 1)).quantize(Decimal('0.01'))
        accumulated_capital += weekly_gain

        # Progress (percentage gain from initial capital)
        progress = 0

        # Create WeeklyGoalReport entry
        weekly_goal = WeeklyGoalReport.objects.create(
            user=user,
            plan_id=plan_id,
            week_number=week_number,
            start_date=monday_date,
            end_date=friday_date,
            accumulated_capital=accumulated_capital,
            gained_amount=weekly_gain,
            progress=progress,
            is_achieved=False,  # This can be updated later
        )

        # Daily calculations and entries
        daily_gain = Decimal((weekly_gain / 5).quantize(Decimal('0.01')))  # Ensure Decimal
        for day in range(5):
            daily_date = monday_date + timedelta(days=day)
            day_capital =Decimal( accumulated_capital - (5 - day) * daily_gain)

            DailyGoalReport.objects.create(
                user=user,
                weekly_goal=weekly_goal,
                plan_id=plan_id,
                day_number=(week_number - 1) * 5 + day + 1,
                date=daily_date,
                capital=day_capital,
                gained_amount=daily_gain,
                progress=0,
                is_achieved=False,  # This can be updated later
            )

        # Move to the next week's Monday
        current_date += timedelta(days=7)

    # Mark the trading plan as active
    trading_plan.is_active = True
    trading_plan.save()

    return HttpResponse(f"Trading plan '{trading_plan.plan_name}' successfully processed and reports generated.")


from django.shortcuts import render, get_object_or_404
from .models import TradingPlan, WeeklyGoalReport, DailyGoalReport

def view_trade_plan(request, pk):
    """
    View to display the details of a specific trading plan along with its weekly and daily goals.
    """
    # Fetch the trading plan using the primary key
    trading_plan = get_object_or_404(TradingPlan, pk=pk)

    # Fetch related weekly and daily goals
    weekly_goals = WeeklyGoalReport.objects.filter(plan_id=pk).order_by('week_number')
    daily_goals = DailyGoalReport.objects.filter(weekly_goal__plan_id=pk).order_by('date')

    for goal in daily_goals:
        if goal.progress != 0:
            goal.progress_percentage = (goal.progress / goal.gained_amount) * 100
        else:
            goal.progress_percentage = 0  # avoid division by zero

    # Context for rendering
    context = {
        'trading_plan': trading_plan,
        'weekly_goals': weekly_goals,
        'daily_goals': daily_goals,
    }

    return render(request, 'dashboard/view_trade_plan.html', context)



from django.shortcuts import get_object_or_404
from django.http import HttpResponse

def delete_trading_plan(request, plan_id):
    # Fetch the trading plan
    trading_plan = get_object_or_404(TradingPlan, id=plan_id)

    # Retrieve the user associated with the plan
    user = trading_plan.user

    # Delete all DailyGoalReports linked to the WeeklyGoalReports of the plan
    DailyGoalReport.objects.filter(weekly_goal__plan_id=plan_id, user=user).delete()

    # Delete all WeeklyGoalReports associated with the plan
    WeeklyGoalReport.objects.filter(plan_id=plan_id, user=user).delete()

    # Delete the trading plan itself
    trading_plan.delete()

    return HttpResponse(f"Trading plan '{plan_id}' and related reports have been successfully deleted.")




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt  # Exempt from CSRF verification since the request is coming from an external source
def order_postback(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON payload
            data = json.loads(request.body)

            # Print the incoming data for debugging purposes
            print("Received POST data:", data)

            # Respond with a success message
            return JsonResponse({"status": "success", "message": "Data received successfully."}, status=200)

        except json.JSONDecodeError:
            # Handle invalid JSON
            print("Error: Received invalid JSON")
            return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)
    else:
        # Handle non-POST requests
        return JsonResponse({"status": "error", "message": "Only POST requests are allowed."}, status=405)
