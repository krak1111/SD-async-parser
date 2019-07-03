port = '5433'
host = 'localhost'
username = 'postgres'
password = 'spostgres'
db_name = 'scienceforecast'
settings = f'host={host} dbname={db_name} port={port} password={password} user={username}'
async_settings = {'host': host, 'port': port, 'user': username, 'password': password, 'database': db_name}