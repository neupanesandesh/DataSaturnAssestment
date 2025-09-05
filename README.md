# Project Setup Instructions

## Step 1: Clone the repo

```bash
git clone https://github.com/username/repo-name.git
```

## Step 2: Projects included

* **Task 1** → `projectmgmt`
* **Task 2** → `dbopt`
* **Task 3** → `authentications`
* **Task 4** → *not included*

---

## Step 3: Environment setup

You can run the project in two ways:

### Option 1: Using Docker

```bash
docker compose build
```

### Option 2: Without Docker

```bash
pip install -r requirements.txt
```

---

## Step 4: Django setup

Run the following commands:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Step 5: Admin panel

* Go to: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
* Login with the superuser you created.
* From here, you can create:

  * Clients
  * Projects
  * Tasks
  * Comments

👉 Role-based membership is available, but you can ignore it if not needed.

---

## Step 6: API endpoints

Base URL: [http://127.0.0.1:8000/api](http://127.0.0.1:8000/api)

* **Clients**

  ```
  /api/clients/{client_id}
  ```

* **Projects of a Client**

  ```
  /api/clients/{client_id}/projects/{id}
  ```

* **Tasks of a Project**

  ```
  /api/clients/{client_id}/projects/{id}/tasks/{id}
  ```

* **Comments of a Task**

  ```
  /api/client/{client_id}/project/{project_id}/tasks/{task_id}/comments/{id}/
  ```

✅ Everything you create in the admin panel (SQLite DB) will show up in these APIs.

---

## Step 7: Task details

* **Task 1:** Project & task management with APIs
* **Task 2:** Database migration + indexing (runs during `makemigrations`)
* **Task 3:** Authentication (use the same admin credentials for access & refresh tokens)
