from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import requests
import atexit
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from dhanhq import dhanhq
from account.models import Control, DhanKillProcessLog
from datetime import datetime
from django.db.models import F
User = get_user_model()

def auto_order_count_monitoring_process():
    now = datetime.now()
    print(f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    if now.weekday() < 5 and (9 <= now.hour < 16):  # Monday to Friday, 9 AM to 4 PM
        try:
            print("**********************************************")
            print("Starting auto order count monitoring process.")
            active_users = User.objects.filter(is_active=True,kill_switch_2=False)
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

            print("No User Found.(May be Killed Already/Not Active)")
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
        elif control_data.peak_order_limit <= traded_order_count and user.kill_switch_1 and not user.kill_switch_2 :
            print(f"WARNING: Peak order limit exceeded for user {user.username}: Limit = {control_data.peak_order_limit}, Traded = {traded_order_count}")
            activate_kill_switch(user, dhan_access_token, traded_order_count)
        elif user.kill_switch_2 :
            print(f"INFO: Kill Switch Activated for {user.username}: Count = {traded_order_count}, Limit = {control_data.max_order_limit}")
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
            if user.kill_switch_1 == False and user.kill_switch_2 == False :
                DhanKillProcessLog.objects.create(user=user, log=response.json(), order_count=traded_order_count)
                user.kill_switch_1 = True
                user.save()
                print(f"INFO: Kill switch 1 activated for user: {user.username}")
            elif user.kill_switch_1 == True and user.kill_switch_2 == False :
                DhanKillProcessLog.objects.create(user=user, log=response.json(), order_count=traded_order_count)
                user.kill_switch_2 = True
                user.save()
                print(f"INFO: Kill switch 2 activated for user: {user.username}")
            elif user.kill_switch_1 == True and user.kill_switch_2 == True :
                print(f"INFO: Kill switch activated for user: {user.username}","Better Luck Next Day")
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

def restore_user_kill_switches():
    active_users = User.objects.filter(is_active=True, kill_switch_1=True, kill_switch_2=True)
    active_users.update(kill_switch_1=False, kill_switch_2=False)
    print(f"INFO: Reset kill switches for {active_users.count()} users.")





def autoStopLossProcessing():
    print("Auto Stop Loss Process Running")
    now = datetime.now()
    print(f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    if now.weekday() < 5 and (9 <= now.hour < 16):  # Monday to Friday, 9 AM to 4 PM
        try:
            print("*********************************************")
            print("Starting auto stoploss monitoring process...!")
            active_users = User.objects.filter(is_active=True,kill_switch_2=False)
            for user in active_users:
                try:
                    if not user.kill_switch_2 and user.auto_stop_loss:
                        dhan_client_id = user.dhan_client_id
                        dhan_access_token = user.dhan_access_token
                        print(f"Processing user: {user.username}, Client ID: {dhan_client_id}")
                        # Fetch control data
                        control_data = Control.objects.filter(user=user).first()
                        stoploss_percentage = float(control_data.stoploss_percentage)
                        # Initialize Dhan client
                        dhan = dhanhq(dhan_client_id, dhan_access_token)
                        order_list = dhan.get_order_list()
                        # Step 1: Sort filtered orders by timestamp in descending order
                        latest_entry = order_list['data'][0]
                        if latest_entry['transactionType'] == 'BUY' and latest_entry['orderStatus'] == 'TRADED':
                            security_id = latest_entry['securityId']
                            client_id = latest_entry['dhanClientId']
                            exchange_segment = latest_entry['exchangeSegment']
                            quantity = latest_entry['quantity']
                            traded_price = float(latest_entry['price'])
                            sl_price, sl_trigger = calculateslprice(traded_price, stoploss_percentage)

                            print("price                                              :", sl_price)
                            print("trigger_price                                      :", sl_trigger)
                            print("Matching order found with details:")
                            print(f"Security ID: {security_id}")
                            print(f"Client ID: {client_id}")
                            print(f"Exchange Segment: {exchange_segment}")
                            print(f"Quantity: {quantity}")

                            pending_sl_orders = get_pending_order_filter_dhan(orderlistdata)
                            if pending_sl_orders:
                                for order in pending_sl_orders:
                                    exst_qty = int(order['quantity'])
                                    addon_qty = int(quantity)
                                    total_qty = exst_qty + addon_qty
                                    modify_slorder_response = dhan.modify_order(
                                                                order_id = order['orderId'], 
                                                                quantity=total_qty
                                                                )

                                print("Stop Loss Modified Response :", modify_slorder_response)
                                print(f"INFO: Stop Loss Order Modified Successfully..!")

                            else:
                                # Place an order for NSE Futures & Options
                                stoploss_response = dhan.place_order(
                                            security_id=security_id, 
                                            exchange_segment=dhan.NSE_FNO,
                                            transaction_type=dhan.SELL,
                                            quantity=quantity,
                                            order_type=dhan.STOP_LOSS,
                                            product_type=dhan.INTRA,
                                            price=sl_price,
                                            trigger_price=sl_trigger
                                        )
                                print("Stop Loss Response :", stoploss_response)
                                print(f"INFO: Stop Loss Order Executed Successfully..!")

                        else:
                            print(f"INFO: No Open Order for User {user.username}")
                        
                    else:
                        print(f"WARNING: Kill switch already activated twice for user: {user.username}")

                except Exception as e:
                    print(f"ERROR: Error processing user {user.username}: {e}")

            print("No User Found.(May be Killed Already/Not Active)")
            print("Auto Stoplos sMonitoring process completed successfully.")
            return JsonResponse({'status': 'success', 'message': 'Monitoring process completed'})

        except Exception as e:
            print(f"ERROR: Error in  stoploss monitoring process: {e}")
            return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)
    else:
        print("INFO: Current time is outside of the scheduled range.")


def calculateslprice(traded_price, stoploss_percentage):
    sl_price = traded_price * (1 - stoploss_percentage / 100)
    slippage = float(settings.TRIGGER_SLIPPAGE)
    sl_price = round(sl_price / slippage) * slippage
    sl_trigger = sl_price + slippage * 2
    sl_price = round(sl_price, 2)
    sl_trigger = round(sl_trigger, 2)
    return sl_price, sl_trigger

def get_pending_order_filter_dhan(response): 
    # Check if the response contains 'data'
    if 'data' not in response:
        return 0
    pending_sl_orders = [
        order for order in response['data']
        if order.get('orderStatus') == 'PENDING' and order.get('transactionType') == 'SELL'
    ]
    if not pending_sl_orders:
        return False  
    return pending_sl_orders


def start_scheduler():
    scheduler = BackgroundScheduler()

    # Self-ping every 58 seconds
    # scheduler.add_job(self_ping, IntervalTrigger(seconds=58))
    # scheduler.add_job(auto_order_count_monitoring_process, IntervalTrigger(seconds=10))
    # # Restore user kill switches every Monday to Friday at 4:00 PM
    # scheduler.add_job(restore_user_kill_switches, CronTrigger(day_of_week='mon-fri', hour=16, minute=0))

    # # for Test 
    # scheduler.add_job(autoStopLossProcessing, IntervalTrigger(seconds=2))
    scheduler.start()
    print("INFO: Scheduler started.")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


