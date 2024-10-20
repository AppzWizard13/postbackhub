# from apscheduler.schedulers.background import BackgroundScheduler
# from dhanhq import dhanhq
# import logging

# # Dhan client setup (make sure to replace client_id and access_token with real values)

# dhan = dhanhq("your_client_id", "your_access_token")

# def fetch_traded_orders():
#     try:
#         # Fetch the order list
#         response = dhan.get_order_list()

#         # Filter orders with status 'TRADED'
#         traded_orders = [order for order in response if order.get('orderStatus') == 'TRADED']

#         # Log or process the traded orders (for example, you can save them to the database)
#         logging.info(f"Traded Orders: {traded_orders}")

#         # Do further processing, like saving orders to the database if needed
#         # for order in traded_orders:
#         #     # Example: save the order to your database model
#         #     Order.objects.create(**order)

#     except Exception as e:
#         logging.error(f"Error fetching traded orders: {e}")

# # Scheduler configuration
# def start_scheduler():
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(fetch_traded_orders, 'interval', seconds=10)
#     scheduler.start()
