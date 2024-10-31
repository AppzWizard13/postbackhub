from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import requests
import atexit
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from dhanhq import dhanhq
from account.models import Control, DhanKillProcessLog, DailyAccountOverview, TempNotifierTable
from datetime import datetime
from django.db.models import F
User = get_user_model()

def auto_order_count_monitoring_process():
    now = datetime.now()
    print(f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    if now.weekday() < 5 and (9 <= now.hour < 16):  # Monday to Friday, 9 AM to 4 PM
        try:
            print("Starting auto order count monitoring process..................")
            active_users = User.objects.filter(is_active=True, kill_switch_2=False)
            for user in active_users:
                try:
                    if user:
                        dhan_client_id = user.dhan_client_id
                        dhan_access_token = user.dhan_access_token
                        print(f"Processing user: {user.username}, Client ID: {dhan_client_id}")
                        # Initialize Dhan client
                        dhan = dhanhq(dhan_client_id, dhan_access_token)
                        # Fetch order list
                        order_list = dhan.get_order_list()
                        traded_order_count = get_traded_order_count(order_list)
                        print("traded_order_counttraded_order_count", traded_order_count)
                        if traded_order_count > 0:
                            # Fetch control data
                            control_data = Control.objects.filter(user=user).first()
                            if control_data:
                                print(f"Handling order limits for user: {user.username}")
                                handle_order_limits(user, dhan, order_list, traded_order_count, control_data, dhan_access_token)
                            else:
                                print(f"INFO: No control data found for user: {user.username}")
                        else:
                            print(f"INFO: No Orders Placed in  user: {user.username}")
                    else:
                        print(f"INFO: Kill switch already activated twice for user: {user.username}")

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
        print("control_data.peak_order_limit:", control_data.peak_order_limit)
        if traded_order_count >= control_data.max_order_limit and traded_order_count < control_data.peak_order_limit and not user.kill_switch_1 and not user.kill_switch_2:
            print(f"WARNING: Max order limit exceeded for user {user.username}: Limit = {control_data.max_order_limit}, Traded = {traded_order_count}")
            activate_kill_switch(user, dhan_access_token, traded_order_count, switch="kill_switch_1")
        elif traded_order_count >= control_data.peak_order_limit and user.kill_switch_1 and not user.kill_switch_2:
            print(f"WARNING: Peak order limit exceeded for user {user.username}: Limit = {control_data.peak_order_limit}, Traded = {traded_order_count}")
            activate_kill_switch(user, dhan_access_token, traded_order_count, switch="kill_switch_2")
        elif user.kill_switch_2:
            print(f"INFO: Kill Switch 2 Activated for {user.username}: Count = {traded_order_count}, Limit = {control_data.max_order_limit}")
        else:
            print(f"INFO: Order count within limits for user {user.username}: Count = {traded_order_count}, Limit = {control_data.max_order_limit}")


def get_traded_order_count(order_list): 
    if 'data' not in order_list or order_list['data'] == '':
        return 0
    else:
        traded_count = len([order for order in order_list['data'] if order.get('orderStatus') == 'TRADED'])
    if not traded_count:
        return 0  
    return traded_count

def get_pending_order_list_and_count(order_list):
    if 'data' not in order_list:
        return [], 0
    pending_orders = [order for order in order_list['data'] if order.get('orderStatus') == 'PENDING']
    pending_order_ids = [order.get('orderId') for order in pending_orders]
    return pending_order_ids, len(pending_order_ids)


def activate_kill_switch(user, access_token, traded_order_count, switch):
    url = 'https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'access-token': access_token}

    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            DhanKillProcessLog.objects.create(user=user, log=response.json(), order_count=traded_order_count)
            
            if switch == "kill_switch_1":
                user.kill_switch_1 = True
                print(f"INFO: Kill switch 1 activated for user: {user.username}")
            elif switch == "kill_switch_2":
                user.kill_switch_2 = True
                print(f"INFO: Kill switch 2 activated for user: {user.username}")
            
            user.save()
        else:
            print(f"ERROR: Failed to activate kill switch for user {user.username}: Status code {response.status_code}")
    except requests.RequestException as e:
        print(f"ERROR: Error activating kill switch for user {user.username}: {e}")

def self_ping():
    try:
        response = requests.get('https://tradewiz.onrender.com/')
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
            print("Starting Auto Stoploss monitoring process...!")
            active_users = User.objects.filter(is_active=True,kill_switch_2=False, auto_stop_loss=True)
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
                        traded_order_count = get_traded_order_count(order_list)
                        if traded_order_count:
                            latest_entry = order_list['data'][0]
                            if latest_entry['transactionType'] == 'BUY' and latest_entry['orderStatus'] == 'TRADED':
                            # if latest_entry['transactionType'] == 'BUY' and latest_entry['orderStatus'] == 'REJECTED':
                                security_id = latest_entry['securityId']
                                client_id = latest_entry['dhanClientId']
                                exchange_segment = latest_entry['exchangeSegment']
                                quantity = latest_entry['quantity']
                                traded_price = float(latest_entry['price'])
                                # traded_price = 100.0
                                sl_price, sl_trigger = calculateslprice(traded_price, stoploss_percentage)
                                print("***************************************************************************")
                                print("price                                              :", sl_price)
                                print("trigger_price                                      :", sl_trigger)
                                print("Matching order found with details:")
                                print(f"Security ID: {security_id}")
                                print(f"Client ID: {client_id}")
                                print(f"Exchange Segment: {exchange_segment}")
                                print(f"Quantity: {quantity}")
                                print("***************************************************************************")

                                pending_sl_orders = get_pending_order_filter_dhan(order_list)
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
                                                exchange_segment=exchange_segment,
                                                transaction_type='SELL',
                                                quantity=quantity,
                                                order_type='STOP_LOSS',
                                                product_type='INTRADAY',
                                                price=sl_price,
                                                trigger_price=sl_trigger
                                            )
                                    print("Stop Loss Response :", stoploss_response)
                                    print(f"INFO: Stop Loss Order Executed Successfully..!")

                                    tempObj, created = TempNotifierTable.objects.get_or_create(
                                        type="dashboard",
                                        defaults={'status': True} 
                                    )

                                    if not created:
                                        tempObj.status = not tempObj.status
                                        tempObj.save()
                                        print("TempNotifierTable record found. Status toggled.")
                                    else:
                                        print("New TempNotifierTable record created with type='dashboard' and status=True.")

                            else:
                                print(f"INFO: No Open Order for User {user.username}")
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
    sl_trigger = sl_price + slippage * 20
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



def DailyAccountOverviewUpdateProcess():
    active_users = User.objects.filter(is_active=True, kill_switch_2=False)
    
    for user in active_users:
        dhan_client_id = user.dhan_client_id
        dhan_access_token = user.dhan_access_token
        # Initialize the Dhan client
        dhan = dhanhq(dhan_client_id, dhan_access_token)
        # Fetch order list, fund data, and position data
        order_list = dhan.get_order_list()
        fund_data = dhan.get_fund_limits()
        position_data = dhan.get_positions()

        # Initialize variables for calculations
        traded_order_count = get_traded_order_count(order_list) if order_list else 0
        total_realized_profit = 0.0
        total_expense = traded_order_count * float(settings.BROKERAGE_PARAMETER)

        # Extract position data safely
        if position_data and 'data' in position_data:
            positions = position_data['data']
            total_realized_profit = sum(position.get('realizedProfit', 0) for position in positions)
        else:
            logger.warning(f"No position data for user {user.username}. Setting realized profit to 0.")

        # Get balances safely
        opening_balance = float(fund_data['data']['sodLimit']) if fund_data and 'data' in fund_data else 0.0
        closing_balance = float(fund_data['data']['withdrawableBalance']) if fund_data and 'data' in fund_data else 0.0
        
        # Calculate actual profit
        actual_profit = total_realized_profit - total_expense
        
        # Create or update DailyAccountOverview entry
        DailyAccountOverview.objects.create(
            user=user,
            opening_balance=opening_balance,
            pnl_status=total_realized_profit,
            expenses=total_expense,
            closing_balance=closing_balance,
            order_count=traded_order_count
        )
        print(f"INFO: DailyAccountOverview updated successfully for {user.username}")





def start_scheduler():
    scheduler = BackgroundScheduler()

    # Self-ping every 58 seconds
    scheduler.add_job(self_ping, IntervalTrigger(seconds=58))
    scheduler.add_job(auto_order_count_monitoring_process, IntervalTrigger(seconds=10))
    # Restore user kill switches every Monday to Friday at 4:00 PM
    scheduler.add_job(restore_user_kill_switches, CronTrigger(day_of_week='mon-fri', hour=16, minute=0))
    scheduler.add_job(restore_user_kill_switches, CronTrigger(day_of_week='mon-fri', hour=9, minute=0))
    scheduler.add_job(DailyAccountOverviewUpdateProcess, CronTrigger(day_of_week='mon-fri', hour=15, minute=30))
    scheduler.add_job(DailyAccountOverviewUpdateProcess, CronTrigger(day_of_week='mon-fri', hour=23, minute=50))

    

    # to test
    scheduler.add_job(autoStopLossProcessing, IntervalTrigger(seconds=2))
    scheduler.start()
    print("INFO: Scheduler started.")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


