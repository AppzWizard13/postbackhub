from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import requests
import atexit
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from dhanhq import dhanhq
from account.models import Control, DhanKillProcessLog

# Get the user model
User = get_user_model()

def auto_order_count_monitoring_process():
    now = datetime.now()
    print(f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    if now.weekday() < 5 and (9 <= now.hour < 16):  # Monday to Friday, 9 AM to 4 PM
        try:
            print("Starting auto order count monitoring process.")
            active_users = User.objects.filter(is_active=True)

            for user in active_users:
                try:
                    if not user.kill_switch_2:
                        dhan_client_id = user.dhan_client_id
                        dhan_access_token = user.dhan_access_token
                        print(f"Processing user: {user.username}, Client ID: {dhan_client_id}")

                        # Initialize Dhan client
                        dhan = dhanhq(dhan_client_id, dhan_access_token)

                        # Fetch order list
                        order_list = dhan.get_order_list()
                        traded_order_count = get_traded_order_count(order_list)

                        # Fetch control data
                        control_data = Control.objects.filter(user=user).first()
                        if control_data:
                            print(f"Handling order limits for user: {user.username}")
                            handle_order_limits(user, dhan, order_list, traded_order_count, control_data, dhan_access_token)
                        else:
                            print(f"WARNING: No control data found for user: {user.username}")
                    else:
                        print(f"WARNING: Kill switch already activated twice for user: {user.username}")

                except Exception as e:
                    print(f"ERROR: Error processing user {user.username}: {e}")

            print("Monitoring process completed successfully.")
            return JsonResponse({'status': 'success', 'message': 'Monitoring process completed'})

        except Exception as e:
            print(f"ERROR: Error in monitoring process: {e}")
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)
    else:
        print("INFO: Current time is outside of the scheduled range.")

def handle_order_limits(user, dhan, order_list, traded_order_count, control_data, dhan_access_token):
    print(f"Evaluating order limits for user: {user.username}")
    pending_order_ids, pending_order_count = get_pending_order_list_and_count(order_list)

    if control_data.max_order_count_mode:
        if control_data.max_order_limit <= traded_order_count and not user.kill_switch_1:
            print(f"WARNING: Max order limit exceeded for user {user.username}: Limit = {control_data.max_order_limit}, Traded = {traded_order_count}")
            activate_kill_switch(user, dhan_access_token, traded_order_count)
        elif control_data.peak_order_limit <= traded_order_count and user.kill_switch_1:
            print(f"WARNING: Peak order limit exceeded for user {user.username}: Limit = {control_data.peak_order_limit}, Traded = {traded_order_count}")
            activate_kill_switch(user, dhan_access_token, traded_order_count)
        else:
            print(f"INFO: Order count within limits for user {user.username}: Count = {traded_order_count}, Limit = {control_data.max_order_limit}")

def get_traded_order_count(order_list):
    if 'data' not in order_list:
        return 0
    return len([order for order in order_list['data'] if order.get('orderStatus') == 'TRADED'])

def get_pending_order_list_and_count(order_list):
    if 'data' not in order_list:
        return [], 0
    pending_orders = [order for order in order_list['data'] if order.get('orderStatus') == 'PENDING']
    pending_order_ids = [order.get('orderId') for order in pending_orders]
    return pending_order_ids, len(pending_order_ids)

def activate_kill_switch(user, access_token, traded_order_count):
    url = 'https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'access-token': access_token}

    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            DhanKillProcessLog.objects.create(user=user, log=response.json(), order_count=traded_order_count)
            user.kill_switch_1 = True
            user.save()
            print(f"INFO: Kill switch activated for user: {user.username}")
        else:
            print(f"ERROR: Failed to activate kill switch for user {user.username}: Status code {response.status_code}")
    except requests.RequestException as e:
        print(f"ERROR: Error activating kill switch for user {user.username}: {e}")

def self_ping():
    try:
        response = requests.get('https://postback-hub.onrender.com/')
        print(f"INFO: Health check response: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Error in self_ping: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Self-ping every 58 seconds
    scheduler.add_job(self_ping, IntervalTrigger(seconds=58))
    scheduler.add_job(auto_order_count_monitoring_process, IntervalTrigger(seconds=10))


    scheduler.start()
    print("INFO: Scheduler started.")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
