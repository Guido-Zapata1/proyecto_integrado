# Proyecto Reservas (Django)

Sistema de reservas con gestión administrativa, áreas/carreras, adjuntos y dashboard.

## Requisitos
- Python 3.11+ (recomendado)
- pip
- (Opcional) PostgreSQL

## Instalación local
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
