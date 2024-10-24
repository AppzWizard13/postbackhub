from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import logging
import requests
import atexit
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from dhanhq import dhanhq
User = get_user_model()
from account.models import Control, DhanKillProcessLog

logger = logging.getLogger(__name__)

def auto_order_count_monitoring_process():
    try:
        # Fetch all active users
        active_users = User.objects.filter(is_active=True)

        for UserObj in active_users:
            try:
                # Extract client ID and access token
                dhan_client_id = UserObj.dhan_client_id  # Assuming 'client_id' exists
                dhan_access_token = UserObj.dhan_access_token  # Assuming 'dhan_access_token' exists
                logger.info(f"Processing user {UserObj.username}, client_id: {dhan_client_id}")
                print(f"Processing user: {UserObj.username}, client_id: {dhan_client_id}")

                # Initialize dhan instance
                dhan = dhanhq(dhan_client_id, dhan_access_token)

                # Fetch order list
                orderlist = dhan.get_order_list()
                logger.info(f"Fetched order list for {UserObj.username}: {orderlist}")
                print(f"Order list: {orderlist}")

                # Get traded order count
                traded_order_count = get_traded_order_count_dhan(orderlist)
                logger.info(f"Traded order count for {UserObj.username}: {traded_order_count}")

                # Fetch control data for the user
                control_data = Control.objects.filter(user=UserObj).first()
                if control_data:
                    logger.info(f"Control data for {UserObj.username}: {control_data}")
                    if control_data.max_order_count_mode:
                        if control_data.max_order_limit <= traded_order_count and not UserObj.kill_switch_1:
                            # Close pending orders
                            pending_order_ids, pending_order_count = get_pending_order_list_and_count_dhan(orderlist)
                            logger.info(f"Pending order count: {pending_order_count}")
                            if pending_order_count > 0:
                                close_pending_response = closeAllPendingOrders(dhan_client_id, dhan_access_token, pending_order_ids)
                                logger.info(f"Pending orders closed for {UserObj.username}")

                            # Close open positions
                            position_close_response = close_all_open_positions(dhan_client_id, dhan_access_token)
                            logger.info(f"Open positions closed for {UserObj.username}")

                            # Kill dhan process
                            response = dhanKillProcess(UserObj,dhan_access_token, traded_order_count)
                            logger.info(f"Kill switch process response: {response.status_code}")
                            response_json = response.json()
                            kill_switch_status = response_json.get('killSwitchStatus', 'Status not found')
                            return JsonResponse({'status': 'success', 'message': kill_switch_status})

                        elif control_data.peak_order_limit <= traded_order_count and UserObj.kill_switch_1:
                            # Close pending orders
                            pending_order_ids, pending_order_count = get_pending_order_list_and_count_dhan(orderlist)
                            logger.info(f"Pending order count: {pending_order_count}")
                            if pending_order_count > 0:
                                close_pending_response = closeAllPendingOrders(dhan_client_id, dhan_access_token, pending_order_ids)
                                logger.info(f"Pending orders closed for {UserObj.username}")

                            # Close open positions
                            position_close_response = close_all_open_positions(dhan_client_id, dhan_access_token)
                            logger.info(f"Open positions closed for {UserObj.username}")

                            # Kill dhan process
                            response = dhanKillProcess(UserObj,dhan_access_token, traded_order_count)
                            logger.info(f"Kill switch process response: {response.status_code}")
                            response_json = response.json()
                            kill_switch_status = response_json.get('killSwitchStatus', 'Status not found')
                            return JsonResponse({'status': 'success', 'message': kill_switch_status})

                        else:
                            print("everything is Fine Monitoring Ongoing..................................")


            except Exception as e:
                logger.error(f"Error processing user {UserObj.username}: {e}")
                print(f"Error processing user {UserObj.username}: {e}")

        # Return success after processing all users
        return JsonResponse({'status': 'success', 'message': 'Data processed successfully'})

    except Exception as e:
        logger.error(f"Error in auto_order_count_monitoring_process: {e}")
        return JsonResponse({'status': 'error', 'message': 'An error occurred'}, status=500)



def get_traded_order_count_dhan(orderlist):
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^", orderlist)
    # Check if the response contains 'data'
    if 'data' not in orderlist:
        return 0

    # Filter orders with 'orderStatus' as 'TRADED'
    traded_orders = [order for order in orderlist['data'] if order.get('orderStatus') == 'TRADED']

    # Return the count of traded orders
    return len(traded_orders)

def get_pending_order_list_and_count_dhan(orderlist):
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^", orderlist)
    
    # Check if the response contains 'data'
    if 'data' not in orderlist:
        return [], 0

    # Filter orders with 'orderStatus' as 'PENDING'
    pending_orders = [order for order in orderlist['data'] if order.get('orderStatus') == 'PENDING']

    # Extract the 'orderId' of pending orders
    pending_order_ids = [order.get('orderId') for order in pending_orders]

    # Return the list of pending order IDs and their count
    return pending_order_ids, len(pending_order_ids)



def dhanKillProcess(UserObj,access_token,traded_order_count):
    url = 'https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'access-token': access_token
    }

    response = requests.post(url, headers=headers)
    print("Response object:", response)
    print("Response content:", response.content)  # Print raw bytes of the response
    print("Response text:", response.text)
    if response.status_code == 200:
        print("Kill switch activated successfully.")
        # Create a log entry in DhanKillProcessLog
        DhanKillProcessLog.objects.create(
            user=UserObj,
            log=response.json(),  # Storing the response as JSON
            order_count=traded_order_count    )

        if not UserObj.kill_switch_1 :
            UserObj.kill_switch_1 = True
            UserObj.save() 
        elif UserObj.kill_switch_1 and not UserObj.kill_switch_2 :
            UserObj.kill_switch_2 = True
            UserObj.save() 

    else:
        print(f"Failed to activate kill switch: {response.status_code}")
    
    return response


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


def closeAllPendingOrders(dhan_client_id, dhan_access_token, pending_order_ids):
    # close all pending orders
    dhan = dhanhq(dhan_client_id,dhan_access_token)
    for order_id in pending_order_ids:
        close_response = dhan.cancel_order(order_id)
    return True
    

def close_all_open_positions(dhan_client_id, dhan_access_token):
    # Initialize Dhan API client
    dhan = dhanhq(dhan_client_id, dhan_access_token)
    
    # Fetch open positions from Dhan API
    open_positions = dhan.get_positions()
    
    if open_positions['status'] == 'success' and open_positions['data']:
        # Loop through each position in the response data
        for position in open_positions['data']:
            security_id = position['securityId']
            exchange_segment = position['exchangeSegment']
            net_qty = position['netQty']
            product_type = position['productType']

            # Map product type
            product_type_map = {
                "CNC": dhan.CNC,
                "DAY": dhan.INTRA
            }
            product_type_value = product_type_map.get(product_type, dhan.CNC)

            # Map exchange segment
            exchange_segment_value = dhan.NSE_FNO if exchange_segment == "NSE_FNO" else exchange_segment

            # Ensure that we are placing a sell order for positions with netQty > 0
            if net_qty > 0:
                # Place a sell order for each open position
                sell_order_response = dhan.place_order(
                    security_id=security_id,
                    exchange_segment=exchange_segment_value,
                    transaction_type=dhan.SELL,  # Sell order
                    quantity=net_qty,
                    order_type=dhan.MARKET,
                    product_type=product_type_value,  # Product type based on position
                    price=0  # Price set to market
                )

                # Check the response of each sell order
                if sell_order_response['status'] != 'success':
                    print(f"Failed to place sell order for security ID {security_id}")
                else:
                    print(f"Successfully placed sell order for security ID {security_id}")

        return True
    else:
        print("No open positions found or failed to fetch open positions.")
        return True


def self_ping():
    try:
        response = requests.get('https://postback-hub.onrender.com/')
        logger.info(f"Health check response: {response.status_code}")
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", response.status_code)
    except Exception as e:
        logger.error(f"Error in self_ping: {e}")
        print("--------------------------------------------------")

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(self_ping, IntervalTrigger(seconds=58))  # Run every 3 seconds
    scheduler.add_job(auto_order_count_monitoring_process, IntervalTrigger(seconds=30))  # Run every 3 seconds
    scheduler.start()
    logger.info("Scheduler started.")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
