from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import requests
import atexit
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from dhanhq import dhanhq
from account.models import Control, DhanKillProcessLog, DailyAccountOverview, TempNotifierTable, slOrderslog
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
    
    # Check if 'data' key is in order_list and that 'data' is a list
    if 'data' not in order_list or not isinstance(order_list['data'], list) or not order_list['data']:
        return 0
    
    # Calculate traded_count if data list is not empty
    traded_count = len([order for order in order_list['data'] if order.get('orderStatus') == 'TRADED'])
    return traded_count if traded_count else 0

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

def autoStopLossProcess():
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
                                # ---------------------------------------------------------------------------------------
                                trading_symbol = latest_entry['tradingSymbol']
                                security_id = latest_entry['securityId']
                                client_id = latest_entry['dhanClientId']
                                exchange_segment = latest_entry['exchangeSegment']
                                quantity = latest_entry['quantity']
                                traded_price = float(latest_entry['price'])
                                # ---------------------------------------------------------------------------------------
                                if control_data.max_lot_size_mode:
                                    get_actual_count = actuallotsizeCalc(trading_symbol,quantity)
                                    if control_data.max_lot_size_limit > get_actual_count:
                                        quantity = get_actual_count - control_data.max_lot_size_limit
                                        quantity = actuallotsizeCalc(trading_symbol,control_data.max_lot_size_limit )
                                        # Place an order for NSE Futures & Options
                                        sellOrderResponse = dhan.place_order(
                                                    security_id=security_id, 
                                                    exchange_segment=exchange_segment,
                                                    transaction_type='SELL',
                                                    quantity=auto_sell_qty,
                                                    order_type='MARKET',
                                                    product_type='INTRADAY',
                                                    price=0
                                                )
                                        print("LOT SIZE controller Executed: for user : ", user , sellOrderResponse)
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
                                                                order_type = order['orderType'],
                                                                quantity=total_qty,
                                                                validity=order["validity"]
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

                                    print("Stop Loss Response:", stoploss_response)
                                    print("INFO: Stop Loss Order Executed Successfully..!")

                                    # Check if the response was successful and contains an order ID
                                    if stoploss_response.get("status") == "success" and "data" in stoploss_response and user.sl_control_mode:
                                        order_id = stoploss_response["data"].get("orderId")
                                        print(f"INFO: Stop Loss Order Executed Successfully..! Order ID: {order_id}")
                                        
                                        # Save the order details in slOrderslog model
                                        sl_order = slOrderslog(
                                            order_id=order_id,
                                            security_id=security_id,
                                            exchange_segment=exchange_segment,
                                            transaction_type='SELL',
                                            quantity=quantity,
                                            order_type='STOP_LOSS',
                                            product_type='INTRADAY',
                                            price=sl_price,
                                            trigger_price=sl_trigger
                                        )
                                        sl_order.save()
                                        print("INFO: Order details saved to slOrderslog successfully.")

                                    else:
                                        print("ERROR: Failed to place stop loss order. Response:", stoploss_response)
                                    
                            elif latest_entry['transactionType'] == 'SELL' and latest_entry['orderStatus'] == 'PENDING' and user.sl_control_mode:
                                latest_order_order_id = latest_entry['orderId']
                                latest_order_price = latest_entry['price']
                                latest_order_type = latest_entry['orderType']
                                latest_order_validity = latest_entry['validity']


                                slModifyCheckData = slOrderslog.Objects.filter(order_id=latest_order_order_id).get()
                                if slModifyCheckData.price <= latest_order_price :
                                    print(f"INFO: Everyhting is good in Stop Loss Monitoring: {user.username}")
                                else:
                                    modify_slorder_response = dhan.modify_order(
                                                        order_id = latest_order_order_id, 
                                                        price = slModifyCheckData.price,
                                                        trigger_price = slModifyCheckData.trigger_price,
                                                        order_type = latest_order_type,
                                                        validity=latest_order_validity
                                                        )      
                                    print(f"INFO: Stop Loss Control Processed: {modify_slorder_response}")

                                print(f"INFO: No Open Order for User {user.username}")

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

def actuallotsizeCalc(tradingSymbol, Qty):
    if tradingSymbol.startswith("NIFTY"):
        actual_qty = Qty / 25
    elif tradingSymbol.startswith("MIDCPNIFTY"):
        actual_qty = Qty / 50
    elif tradingSymbol.startswith("FINNIFTY"):
        actual_qty = Qty / 50
    elif tradingSymbol.startswith("BANKNIFTY"):
        actual_qty = Qty / 15
    else:
        actual_qty = Qty
    return actual_qty

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
    # Get the current hour
    current_hour = datetime.now().hour
    
    # Set flags for the opening and closing runs
    is_first_run = current_hour == 9
    is_last_run = current_hour == 16
    
    # Query active users
    active_users = User.objects.filter(is_active=True)
    
    for user in active_users:
        try:
            dhan_client_id = user.dhan_client_id
            dhan_access_token = user.dhan_access_token

            # Initialize the Dhan client
            dhan = dhanhq(dhan_client_id, dhan_access_token)
            
            # Fetch data
            order_list = dhan.get_order_list() or []
            fund_data = dhan.get_fund_limits()
            position_data = dhan.get_positions()
            
            # Calculate traded orders and expenses
            traded_order_count = get_traded_order_count(order_list)
            total_realized_profit = 0.0
            total_expense = traded_order_count * float(settings.BROKERAGE_PARAMETER)
            # Process position data safely
            if position_data and 'data' in position_data:
                positions = position_data['data']
                total_realized_profit = sum(position.get('realizedProfit', 0) for position in positions)
            else:
                logger.warning(f"No position data for user {user.username}. Setting realized profit to 0.")

            # Calculate balances safely
            opening_balance = float(fund_data['data'].get('sodLimit', 0.0)) if fund_data and 'data' in fund_data else 0.0
            closing_balance = float(fund_data['data'].get('withdrawableBalance', 0.0)) if fund_data and 'data' in fund_data else 0.0
            
            # Calculate actual profit
            actual_profit = total_realized_profit - total_expense
            
            # Set day_open and day_close fields based on the time of day
            day_open = is_first_run
            day_close = is_last_run
            
            # Create or update the DailyAccountOverview entry
            DailyAccountOverview.objects.create(
                user=user,
                opening_balance=opening_balance,
                pnl_status=total_realized_profit,
                actual_profit = actual_profit,
                expenses=total_expense,
                closing_balance=closing_balance,
                order_count=traded_order_count,
                day_open=day_open,
                day_close=day_close
            )
            
            print(f"INFO: DailyAccountOverview updated successfully for {user.username}")
        
        except Exception as e:
            print(f"INFO: Error processing user  for  {user.username}: {e}")
            continue  # Skip to the next user

def autoclosePositionProcess():
    print("Auto Close Positions Process Running")
    now = datetime.now()
    print(f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    if now.weekday() < 5 and (9 <= now.hour < 16):  # Monday to Friday, 9 AM to 4 PM
        try:
            print("Starting Auto close position  monitoring process...!")
            active_users = User.objects.filter(is_active=True, kill_switch_2=False, quick_exit=True)
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
                            sl_order_id = latest_entry['orderId']
                            if latest_entry['transactionType'] == 'SELL' and latest_entry['orderStatus'] == 'CANCELLED':
                                security_id = latest_entry['securityId']
                                client_id = latest_entry['dhanClientId']
                                exchange_segment = latest_entry['exchangeSegment']
                                quantity = latest_entry['quantity']
                                traded_price = float(latest_entry['price'])
                                print("***************************************************************************")
                                print("SELL ORDER PAYLOAD DATA:")
                                print(f"Security ID: {security_id}")
                                print(f"Client ID: {client_id}")
                                print(f"Exchange Segment: {exchange_segment}")
                                print(f"Quantity: {quantity}")
                                print("***************************************************************************")
                                # Place an order for NSE Futures & Options
                                sellOrderResponse = dhan.place_order(
                                            security_id=security_id, 
                                            exchange_segment=exchange_segment,
                                            transaction_type='SELL',
                                            quantity=quantity,
                                            order_type='MARKET',
                                            product_type='INTRADAY',
                                            price=0
                                        )
                                print("SELL ORDER Response :", sellOrderResponse)
                                slOrderslog.objects.filter(order_id=sl_order_id).delete()
                                print(f"INFO: Position Closing Executed Successfully..!")


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



def autoAdminSwitchingProcess():
    try:
        # Get the current time
        current_hour = datetime.now().hour
        if current_hour == 9:
            # Set vicky as superuser and remove superuser status from juztin and tradingwitch every day at 9 AM
            acting_admin = settings.ACTING_ADMIN
            acting_traders_list = settings.ACTING_TRADERS
            vicky = User.objects.get(username=acting_admin)
            vicky.is_superuser = True
            vicky.save()
            print(f"INFO: Set", acting_admin, "as superuser at 9 AM")

            for username in acting_traders_list:
                user = User.objects.get(username=username)
                user.is_superuser = False
                user.save()
                print(f"INFO: Removed superuser status from '{username}'")

        elif current_hour == 16:
            # Set tradingwitch as superuser and remove superuser status from vicky every day at 4 PM
            dev_admin = settings.DEV_ADMIN
            tradingwitch = User.objects.get(username=dev_admin)
            tradingwitch.is_superuser = True
            tradingwitch.save()
            print("INFO: Set", dev_admin, "as superuser at 4 PM")

            vicky = User.objects.get(username='vicky')
            vicky.is_superuser = False
            vicky.save()
            print("INFO: Removed superuser status from 'vicky'")

        else:
            print("Admin Switching Process not in time range")

    except User.DoesNotExist as e:
        print(f"ERROR: User not found: {e}")
    except Exception as e:
        print(f"ERROR: An error occurred in update_superuser_status: {e}")




def autoMaxlossMaxProfitKillProcess():
    """Monitors and activates the kill switch for users based on max loss or profit limits."""
    print("Auto Max loss kill Process Running")
    now = datetime.now()
    print(f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # Ensure execution only on weekdays from 9 AM to 4 PM
    if not (now.weekday() < 5 and 9 <= now.hour < 16):
        print("INFO: Process is only running Monday to Friday, from 9 AM to 4 PM.")
        return

    try:
        print("Starting Auto Max loss kill monitoring process...!")
        active_users = User.objects.filter(is_active=True, kill_switch_2=False, quick_exit=True)
        
        for user in active_users:
            if user.kill_switch_2 or not user.auto_stop_loss:
                continue
            print(f"Processing user: {user.username}, Client ID: {user.dhan_client_id}")
            process_user(user)
            
    except Exception as e:
        print(f"ERROR in autoMaxlossMaxProfitKillProcess: {e}")


def process_user(user):
    """Processes a single user for kill switch activation based on max loss/profit limits."""
    try:
        control_data = Control.objects.filter(user=user).first()
        if not control_data:
            print(f"INFO: Control data not found or max loss mode disabled for User {user.username}")
            return
        
        positions = get_positions(user.dhan_access_token)
        if not positions:
            print(f"INFO: No positions found for User {user.username}")
            return
        
        total_realized_profit = sum(position['realizedProfit'] for position in positions)
        total_realized_profit = abs(total_realized_profit) if total_realized_profit < 0 and control_data.max_loss_mode else total_realized_profit
        
        # Check max loss and profit conditions
        if control_data.max_loss_mode and total_realized_profit > control_data.max_loss_limit:
            if total_realized_profit > control_data.peak_loss_limit:
                print(f"INFO: Peak loss exceeded for User {user.username}. Activating kill switch.")
                activate_kill_switch_process(user)
            else:
                print(f"INFO: Max loss exceeded for User {user.username}. Activating kill switch.")
                activate_kill_switch_process(user)
        elif control_data.max_profit_mode and total_realized_profit > control_data.max_profit_limit:
            print(f"INFO: Max Profit exceeded for User {user.username}. Activating kill switch.")
            activate_kill_switch_process(user)
        else:
            print(f"INFO: Positive/Good Earning status for User {user.username}")

    except Exception as e:
        print(f"ERROR processing user {user.username}: {e}")


def get_positions(access_token):
    """Fetches positions for a user from the Dhan API."""
    try:
        position_data = dhan.get_positions()
        return position_data['data'] if 'data' in position_data and isinstance(position_data['data'], list) and position_data['data'] else None
    except Exception as e:
        print(f"ERROR fetching positions: {e}")
        return None


def activate_kill_switch_process(user):
    """Activates the kill switch for a user and logs the action."""
    url = 'https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'access-token': user.dhan_access_token}

    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            log_kill_switch_action(user, response.json())
            update_user_kill_switch(user)
        else:
            print(f"ERROR: Failed to activate kill switch for user {user.username}: Status code {response.status_code}")
    except requests.RequestException as e:
        print(f"ERROR: Error activating kill switch for user {user.username}: {e}")


def log_kill_switch_action(user, response_data):
    """Logs the kill switch activation."""
    DhanKillProcessLog.objects.create(user=user, log=response_data, order_count=0)


def update_user_kill_switch(user):
    """Updates the user's kill switch status."""
    if not user.kill_switch_1:
        user.kill_switch_1 = True
        print(f"INFO: Kill switch 1 activated for user: {user.username}")
    else:
        user.kill_switch_2 = True
        print(f"INFO: Kill switch 2 activated for user: {user.username}")
    user.save()



def start_scheduler():
    scheduler = BackgroundScheduler()

    # Self-ping every 58 seconds
    scheduler.add_job(self_ping, IntervalTrigger(seconds=180))

    
    scheduler.add_job(auto_order_count_monitoring_process, IntervalTrigger(seconds=10))



    # Restore user kill switches every Monday to Friday at 4:00 PM
    scheduler.add_job(restore_user_kill_switches, CronTrigger(day_of_week='mon-fri', hour=16, minute=0))
    scheduler.add_job(restore_user_kill_switches, CronTrigger(day_of_week='mon-fri', hour=9, minute=0))
    scheduler.add_job(DailyAccountOverviewUpdateProcess, CronTrigger(day_of_week='mon-fri', hour='9-16', minute=0))
    # Schedule the job to run every 10 seconds for testing

    # to test
    scheduler.add_job(autoStopLossProcess, IntervalTrigger(seconds=1))
    scheduler.add_job(autoStopLossProcess, IntervalTrigger(seconds=10))
    scheduler.add_job(autoclosePositionProcess, IntervalTrigger(seconds=2))
    scheduler.add_job(autoAdminSwitchingProcess, IntervalTrigger(hours=1))
    scheduler.add_job(autoMaxlossMaxProfitKillProcess, IntervalTrigger(seconds=2))


    







    
    scheduler.start()
    print("INFO: Scheduler started.")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


