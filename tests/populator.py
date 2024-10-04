import requests

base_url = 'http://127.0.0.1:8000'

test_user_creds = [
    {'username': 'test_user',
     'password': 'qwerty1234',
     'email': 'test@email.com'},
    {'username': 'test2_user',
     'password': 'qwerty1234',
     'email': 'test2@email.com'},
    {'username': 'good_user',
     'password': 'qwerty1234',
     'email': 'good@gmail.com'},
]


if __name__ == '__main__':
    for user in test_user_creds:
        resp = requests.post(f'{base_url}/auth/register', json=user)
        if resp.status_code == 201:
            print(f'User {user["username"]} created')
        else:
            print(f'Failed to create user {user["username"]}. [{resp.status_code}] {resp.text}')
