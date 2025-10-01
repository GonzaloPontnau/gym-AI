#!/usr/bin/env python
"""
Script de diagnóstico para verificar la salud de la aplicación GymAI
antes de desplegar a Render.

Uso: python check_health.py
"""
import sys
import os
import asyncio

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_imports():
    """Verificar que todas las dependencias se puedan importar"""
    print("🔍 Verificando imports...")
    
    required_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("aiosqlite", "AIOSQLite"),
        ("dotenv", "python-dotenv"),
    ]
    
    optional_modules = [
        ("google.generativeai", "Google Generative AI (Gemini)"),
        ("PIL", "Pillow (procesamiento de imágenes)"),
        ("asyncpg", "AsyncPG (PostgreSQL)"),
    ]
    
    all_ok = True
    
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError as e:
            print(f"  ❌ {display_name} - Error: {e}")
            all_ok = False
    
    print("\n🔍 Verificando módulos opcionales...")
    for module_name, display_name in optional_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError:
            print(f"  ⚠️  {display_name} (opcional - no instalado)")
    
    return all_ok

def check_env_vars():
    """Verificar variables de entorno"""
    print("\n🔍 Verificando variables de entorno...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Variables opcionales pero recomendadas
    env_vars = {
        "GEMINI_API_KEY": "API Key de Google Gemini (para IA)",
        "DATABASE_URL": "URL de la base de datos",
        "SECRET_KEY": "Clave secreta (seguridad)"
    }
    
    for var_name, description in env_vars.items():
        value = os.environ.get(var_name)
        if value:
            # Mostrar solo los primeros caracteres para seguridad
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var_name}: {masked} - {description}")
        else:
            print(f"  ⚠️  {var_name} no configurada - {description}")
    
    # Verificar si Gemini está configurado
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("\n  ⚠️  ADVERTENCIA: GEMINI_API_KEY no configurada")
        print("     La funcionalidad de IA no estará disponible")
        print("     Configúrala en el archivo .env o variables de entorno")

def check_app_structure():
    """Verificar estructura de archivos"""
    print("\n🔍 Verificando estructura de archivos...")
    
    required_files = [
        "app/main.py",
        "app/models/models.py",
        "app/db/database.py",
        "app/services/gemini_service.py",
        "requirements.txt",
        "render.yaml",
        "templates/base.html",
        "templates/chat_initial.html",
        "templates/dashboard.html",
    ]
    
    all_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - FALTA")
            all_ok = False
    
    return all_ok

async def check_app_startup():
    """Intentar iniciar la aplicación"""
    print("\n🔍 Verificando inicio de la aplicación...")
    
    try:
        from app.main import app
        print("  ✅ Aplicación FastAPI creada correctamente")
        
        # Verificar que el health check endpoint existe
        routes = [route.path for route in app.routes]
        if "/health" in routes:
            print("  ✅ Endpoint /health configurado")
        else:
            print("  ❌ Endpoint /health NO encontrado")
            return False
        
        # Verificar otros endpoints importantes
        if "/" in routes:
            print("  ✅ Endpoint / (raíz) configurado")
        
        return True
    except Exception as e:
        print(f"  ❌ Error al crear aplicación: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_database():
    """Verificar conexión a base de datos"""
    print("\n🔍 Verificando base de datos...")
    
    try:
        from app.db.database import engine, IS_SQLITE, DB_URL
        from sqlalchemy import text
        
        print(f"  ℹ️  Tipo de BD: {'SQLite' if IS_SQLITE else 'PostgreSQL'}")
        
        # Mostrar URL de forma segura
        if IS_SQLITE:
            print(f"  ℹ️  URL: {DB_URL}")
        else:
            # Ocultar credenciales en URL de PostgreSQL
            masked_url = DB_URL.split('@')[1] if '@' in DB_URL else DB_URL[:30] + "..."
            print(f"  ℹ️  URL: ...@{masked_url}")
        
        # Intentar conectar
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        print("  ✅ Conexión a base de datos exitosa")
        return True
        
    except Exception as e:
        print(f"  ❌ Error de conexión a BD: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_render_config():
    """Verificar configuración de Render"""
    print("\n🔍 Verificando configuración de Render (render.yaml)...")
    
    import yaml
    
    try:
        with open("render.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        service = config['services'][0]
        
        # Verificar configuraciones importantes
        checks = [
            ("type", "web", "Tipo de servicio"),
            ("env", "python", "Entorno Python"),
            ("healthCheckPath", "/health", "Health check endpoint"),
        ]
        
        all_ok = True
        for key, expected, description in checks:
            value = service.get(key)
            if value == expected:
                print(f"  ✅ {description}: {value}")
            else:
                print(f"  ⚠️  {description}: {value} (esperado: {expected})")
                all_ok = False
        
        # Verificar comando de inicio
        start_cmd = service.get('startCommand', '')
        if 'gunicorn' in start_cmd and 'app.main:app' in start_cmd:
            print(f"  ✅ Comando de inicio correcto")
        else:
            print(f"  ⚠️  Comando de inicio podría tener problemas")
            print(f"     {start_cmd}")
        
        return all_ok
        
    except FileNotFoundError:
        print("  ❌ render.yaml no encontrado")
        return False
    except Exception as e:
        print(f"  ❌ Error al leer render.yaml: {e}")
        return False

async def main():
    """Función principal de diagnóstico"""
    print("=" * 60)
    print("🏋️ DIAGNÓSTICO DE SALUD - GymAI")
    print("=" * 60)
    
    results = []
    
    # Ejecutar todas las verificaciones
    results.append(("Imports", check_imports()))
    check_env_vars()  # Solo informativo
    results.append(("Estructura de archivos", check_app_structure()))
    results.append(("Inicio de aplicación", await check_app_startup()))
    results.append(("Base de datos", await check_database()))
    results.append(("Configuración Render", check_render_config()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    all_passed = all(result for _, result in results)
    
    for check_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("\n🚀 Tu aplicación está lista para desplegar a Render")
        print("\nPróximos pasos:")
        print("1. Asegúrate de configurar GEMINI_API_KEY en Render")
        print("2. Haz push a GitHub: git push origin master")
        print("3. Render desplegará automáticamente")
        print("4. Verifica el health check: https://tu-app.onrender.com/health")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("\n⚠️  Revisa los errores arriba antes de desplegar")
        print("\nPasos recomendados:")
        print("1. Instala dependencias faltantes: pip install -r requirements.txt")
        print("2. Configura variables de entorno en archivo .env")
        print("3. Verifica que todos los archivos existan")
        print("4. Ejecuta este script nuevamente")
        
        sys.exit(1)

if __name__ == "__main__":
    # Ejecutar diagnóstico
    asyncio.run(main())

