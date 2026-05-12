from fastapi import FastAPI
from faker import Faker
import random

app = FastAPI(title="API de Facturas Fake", version="1.0")

fake = Faker("es_ES")


@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido a la API de Facturas Fake",
        "version": "1.0",
        "rutas_disponibles": {
            "raiz": "/",
            "obtener_factura": "/facturas/v1/{numero_factura}"
        }
    }


@app.get("/facturas/v1/{numero_factura}")
def get_factura(numero_factura: str):
    
    empresa = {
        "nombre": fake.company(),
        "direccion": fake.address(),
        "telefono": fake.phone_number(),
        "email": fake.company_email()
    }

    cliente = {
        "nombre": fake.company(),
        "direccion": fake.address(),
        "telefono": fake.phone_number()
    }

   
    detalle = []
    for _ in range(random.randint(1, 5)):
        cantidad = random.randint(1, 10)
        precio_unitario = round(random.uniform(50, 500), 2)
        total = round(cantidad * precio_unitario, 2)
        detalle.append({
            "descripcion": fake.catch_phrase(),
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "total": total
        })

    subtotal = round(sum(item["total"] for item in detalle), 2)
    impuesto = round(subtotal * 0.21, 2)  # IVA 21%
    total = round(subtotal + impuesto, 2)

    factura = {
        "numero_factura": numero_factura,
        "fecha_emision": str(fake.date_between(start_date="-1y", end_date="today")),
        "empresa": empresa,
        "cliente": cliente,
        "detalle": detalle,
        "subtotal": subtotal,
        "impuesto": impuesto,
        "total": total
    }

    return factura

