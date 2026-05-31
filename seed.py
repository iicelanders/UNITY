"""
seed.py — One-time script to populate inventario_herramientas (§6.7).

Run this once before testing: python seed.py

If Supabase is not configured, it prints the data that would be inserted.
"""

import os
from dotenv import load_dotenv

load_dotenv()

TOOLS = [
    {"nombre_herramienta": "Palas", "cantidad_total": 20, "cantidad_disponible": 20},
    {"nombre_herramienta": "Cascos", "cantidad_total": 30, "cantidad_disponible": 30},
    {"nombre_herramienta": "Botiquines", "cantidad_total": 15, "cantidad_disponible": 15},
    {"nombre_herramienta": "Radios", "cantidad_total": 10, "cantidad_disponible": 10},
    {"nombre_herramienta": "Linternas", "cantidad_total": 25, "cantidad_disponible": 25},
    {"nombre_herramienta": "Guantes", "cantidad_total": 50, "cantidad_disponible": 50},
]


def main():
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")

    if supabase_url and supabase_key and supabase_url != "your_supabase_url_here":
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)
        result = client.table("inventario_herramientas").insert(TOOLS).execute()
        print(f"✅ {len(result.data)} herramientas insertadas en Supabase.")
    else:
        print("⚠️  Supabase no configurado. Datos que se insertarían:")
        for tool in TOOLS:
            print(f"  - {tool['nombre_herramienta']}: {tool['cantidad_total']} uds.")
        print("\nConfigura SUPABASE_URL y SUPABASE_KEY en .env y vuelve a ejecutar.")


if __name__ == "__main__":
    main()
