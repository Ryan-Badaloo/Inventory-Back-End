## The **Fast-API Computer Inventory Backend System** 


This application is the backend serevice for the Computer Inventory System.
The following tools and Teck are used:
---

## 👥 Author

- [ministry of agriculture fisheries and mining](https://www.moa.gov.jm/)

---

## 🚀 Getting Started (Run Locally)

---

### 1. 📦 Set Up a Virtual Environment
install `virtualenv` using pip, for more infromation on virtualenv [click me](https://virtualenv.pypa.io/en/latest/)
```sh
 pip install virtualenv
```

Create and activate a virtual environment:
```sh
 virtualenv venv
 
 # Windows:
 venv\Scripts\activate

 # macOS/Linux:
 source venv/bin/activate
```

Install all python Packages
```sh
 pip install --upgrade -r requirements.txt
```

Start local FastAPI server
```sh
 uvicorn main:app --reload
```

Generate migrations file with the following command
```sh
 alembic revision --autogenerate -m "commit message"
```

Run migration
```sh
 alembic upgrade head
```

Undo migration
```sh
alembic downgrade -1
```

Update requirements.txt file
```sh
 pip3 freeze > requirements.txt 
```

---
 ## 📁 API Documentation
---
Start local FastAPI server
```sh
 uvicorn main:app --reload
```
Hyperlink to api docs
```sh
    http://127.0.0.1:8000/docs
```

---
 ## 🐳📦💻 Docker
---

###  1. Start dev database Server
```sh
 # start development database
 docker compose up -d

 # stop development database
 docker compose down
```

### 2. 🐳 build docker image
```sh
 docker build -t ictdev2025/computerinventorybackend:tag .
```

### 3. 🐳 push docker image
```bash
 docker push ictdev2025/computerinventorybackend:tag
```