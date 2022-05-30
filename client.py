import requests

url ='http://127.0.0.1:5000'

command = 1
while command != 0:

    command  = int(input(
                'Input command: \n\
                1 - get user by id \n\
                2 - get all users \n\
                3 - add new user \n\
                4 - get all advertisements \n\
                44 - get all advertisements by user_id \n\
                5 - add new advertisement \n\
                6 - delete advertisement \n\
                0 - exit >>>> '))

    def message(response):
        print('STATUS CODE: ',response.status_code)
        print('INFO: ',response.text)

    if command == 1:
        response = requests.get(f'{url}/user/1/')
        message(response)

    elif command == 2:
        response = requests.get(f'{url}/get_users')
        message(response)

    elif command == 3:
        response = requests.post(f'{url}/add_user/',
                            json = {'email': 'peter1@mail.ru', 'user_name': "PetrNEW", 'password': '1234'})
        message(response)

    elif command == 4:
        response = requests.get(f'{url}/get_advertisments/')
        message(response)

    elif command == 44:
        response = requests.get(f'{url}/get_advertisments/?user_id=1')
        message(response)

    elif command == 5:
        response = requests.post(f'{url}/add_adv/',
                            json = {'title': 'title title title', 'description': "description description description", 'user_id': 1})
        message(response)

    elif command == 6:
        response = requests.delete(f'{url}/del_advertisments/1/')
        message(response)



