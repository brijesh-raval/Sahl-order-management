from flask import Flask, request
import firebase_admin
from firebase_admin import firestore
from firebase_admin import db
from firebase_admin import credentials

from firebase import Firebase

app2 = firebase_admin.initialize_app(credentials.Certificate('sahl.json'))

client = firestore.client(app2)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return "HelloWorld"


@app.route('/time', methods=['POST'])
def remaining_time():

    class SJF:            

        def schedulingProcess(self, process_data):
            start_time = []
            exit_time = []
            s_time = 0
            process_data.sort(key=lambda x: x[1])
            '''
            Sort processes according to the Arrival Time
            '''
            for i in range(len(process_data)):
                ready_queue = []
                temp = []
                normal_queue = []


                for j in range(len(process_data)):
                    if (process_data[j][1] <= s_time) and (process_data[j][3] == 0):
                        temp.extend([process_data[j][0], process_data[j][1], process_data[j][2]])
                        ready_queue.append(temp)
                        temp = []
                    elif process_data[j][3] == 0:
                        temp.extend([process_data[j][0], process_data[j][1], process_data[j][2]])
                        normal_queue.append(temp)
                        temp = []


                if len(ready_queue) != 0:
                    ready_queue.sort(key=lambda x: x[2])
                    '''
                    Sort the processes according to the Burst Time
                    '''
                    start_time.append(s_time)
                    s_time = s_time + ready_queue[0][2]
                    e_time = s_time
                    exit_time.append(e_time)
                    for k in range(len(process_data)):
                        if process_data[k][0] == ready_queue[0][0]:
                            break
                    process_data[k][3] = 1
                    process_data[k].append(e_time)


                elif len(ready_queue) == 0:
                    if s_time < normal_queue[0][1]:
                        s_time = normal_queue[0][1]
                    start_time.append(s_time)
                    s_time = s_time + normal_queue[0][2]
                    e_time = s_time
                    exit_time.append(e_time)
                    for k in range(len(process_data)):
                        if process_data[k][0] == normal_queue[0][0]:
                            break
                    process_data[k][3] = 1
                    process_data[k].append(e_time)


            t_time = SJF.calculateTurnaroundTime(self, process_data)
            w_time = SJF.calculateWaitingTime(self, process_data)
            re = SJF.printData(self, process_data, t_time, w_time)
            return re


        def calculateTurnaroundTime(self, process_data):
            total_turnaround_time = 0
            for i in range(len(process_data)):
                turnaround_time = process_data[i][4] - process_data[i][1]
                total_turnaround_time = total_turnaround_time + turnaround_time
                process_data[i].append(turnaround_time)
            average_turnaround_time = 5 # Static # total_turnaround_time / len(process_data)
            return average_turnaround_time


        def calculateWaitingTime(self, process_data):
            total_waiting_time = 0
            for i in range(len(process_data)):
                waiting_time = process_data[i][5] - process_data[i][2]
                total_waiting_time = total_waiting_time + waiting_time
                process_data[i].append(waiting_time)
            average_waiting_time = 5 # Static #total_waiting_time / len(process_data)
            return average_waiting_time


        def printData(self, process_data, average_turnaround_time, average_waiting_time):
            process_data.sort(key=lambda x: x[2])
            re = []
            '''
            Sort processes according to the Burst_Time
            '''
            print("Order_ID  Cust_Arrival_Time  Preparing_Time   Completed  Completion_Time  Turnaround_Time  Waiting_Time")
            re = []
            var = 1
            for i in range(len(process_data)):
                temp = []
                
                for j in range(len(process_data[i])):
                    print(process_data[i][j], end="\t\t")
                
                temp.append(process_data[i][0])
                temp.append(var)
                var = var + 1
                re.append(temp)
                print()
            
            return re


    # Execution started From here, 

    # Getting StoreId from JSON
    storeID = request.json['payload']['storeId']


    # Initializes store collection
    docs = client.collection(u'stores').document(storeID).collection('orders').stream()

    orders = [] # Getting all things in this
    arrival_time = 0 # Static for now



    for doc in docs:

        orderType = doc.to_dict()['data'][0]['order']['details']['order_type']
        if orderType == 'online' or orderType == 'delivery':
            continue
        print("OrderPriority : ", doc.to_dict()['orderPriority'])
        do = client.collection(u'stores').document(storeID).collection('orders').document(doc.id)
        # Updating key
        do.update({u'orderPriority': 0})
        try:
            order_state = doc.to_dict()['data'][4]['order_state']
            if order_state == 'Completed':
                do = client.collection(u'stores').document(storeID).collection('orders').document(doc.id)
                # Updating key
                do.update({u'orderPriority': 1000})
                continue

        except:

            print(f'Order ID : {doc.id}')
            print(f'Order Type : {orderType}')

            # Initilize the order details
            order = []
            production_time = 0
            count = 0

            for i in range(len(doc.to_dict()['data'][0]['order']['items'])):
                print('Order #', doc.id, 'item no. ', i, 'item id ', doc.to_dict()['data'][0]['order']['items'][i]['id'])
                print('item name : ' , doc.to_dict()['data'][0]['order']['items'][i]['title'])
                print(f'item quentity : ', doc.to_dict()['data'][0]['order']['items'][i]['quantity'])
                
                # Geeting Item served or not
                isServed = doc.to_dict()['data'][0]['order']['items'][i]['isServed']
                if isServed == True :
                    count = count + 1
                    continue 
                print('Item is served #', isServed)
                print('Item production time :', doc.to_dict()['data'][0]['order']['items'][i]['productionTime'])

                # Making count of production time of items
                production_time = int(production_time + doc.to_dict()['data'][0]['order']['items'][i]['productionTime']) #* (doc.to_dict()['data'][0]['order']['items'][i]['quantity'] / 2))

            print(f'Total order production time : {production_time}')
            if count == len(doc.to_dict()['data'][0]['order']['items']):
                do = client.collection(u'stores').document(storeID).collection('orders').document(doc.id)
                # Updating key
                do.update({u'orderPriority': 1000})
                continue

            # Gather all data into two dimensional list
            order.append(doc.id)
            order.append(arrival_time)    
            order.append(production_time)    
            order.append(arrival_time)
            orders.append(order)
            print()

    # {order_id} , {arrival_time} , {burst_time} , {'0' is the state of the process. 0 means order not completed and 1 means order completed}
    print('List created after all data preprocessing : ' , orders)
    print()

    # Initializes Object
    sjf = SJF()
    re = sjf.schedulingProcess(orders)

    print()
    print('List after all done : ', re)

    # Getting updating orderPriority key
    document = client.collection(u'stores').document(storeID).collection('orders').stream()
    
    for documents in document:
        for i in range(len(re)):
            do = client.collection(u'stores').document(storeID).collection('orders').document(re[i][0])
            # Updating key
            do.update({u'orderPriority': re[i][1]})

    return {
        "Sucess":"done"
        }


if __name__ == '__main__':
    app.run(debug=True)
