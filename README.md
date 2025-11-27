# backend-chordmaster


## Database with Docker

To run a local MySQL server for this project using Docker compose:

1. Copy or review `.env.db` (example file added) to set credentials and database name.

2. Start MySQL and Adminer:

```bash
docker-compose up -d
```

Adminer will be available at `http://localhost:8080` (use credentials from `.env.db`).

3. Adjust your `DATABASE_URL` in `app/config.py` if needed:

- If you run the Python app on the host (not in Docker), use `127.0.0.1`:
```
mysql+mysqlconnector://chorduser:chordpass@127.0.0.1:3306/railway
```

- If you containerize your app in the same compose network, use the service name `db`:
```
mysql+mysqlconnector://chorduser:chordpass@db:3306/railway
```

4. Create database tables (once DB is ready):

```bash
# activate your virtualenv if needed
source venv/bin/activate
python create_db.py
```

If you prefer, open Adminer and execute the SQL `SHOW TABLES;` or run the script above.
