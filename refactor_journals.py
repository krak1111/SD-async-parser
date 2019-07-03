import psycopg2


from source.DB_SETTINGS import settings



def main():
    connect = psycopg2.connect(settings)
    cur = connect.cursor()

    cur.execute('''ALTER TABLE journals
                     ADD COLUMN IF NOT EXISTS url VARCHAR(100),
                     ADD COLUMN IF NOT EXISTS issn VARCHAR(8),
                     ADD COLUMN IF NOT EXISTS status VARCHAR(15)
                ''')

    cur.execute("UPDATE journals SET status = 'waiting'")
    connect.commit()
    cur.close()
    connect.close()


if __name__ == '__main__':
    main()
