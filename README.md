# Backend developer test task for funbox.ru
### Task text: https://funbox.ru/q/python.pdf
## Getting started
1. Start your redis server:  
`redis-server` or `redis-sever /etc/redis/6379.conf` if you use custom config file
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` file in the root project directory and add your credentials, where:  
`REDIS_HOST=your_redis_host` (defaults to 'localhost')  
`REDIS_PORT=your_redis_port` (defaults to '6379')  
`SECRET_KEY=your_django_secret_key`
4. Run server: `python manage.py runserver`