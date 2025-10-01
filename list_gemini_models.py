#!/usr/bin/env python
"""
Script para listar todos los modelos de Gemini disponibles en tu API key
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    import google.generativeai as genai
    
    # Configurar API key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: GEMINI_API_KEY no encontrada en .env")
        exit(1)
    
    genai.configure(api_key=api_key)
    
    print("=" * 80)
    print("MODELOS DE GEMINI DISPONIBLES EN TU CUENTA")
    print("=" * 80)
    print()
    
    # Listar todos los modelos
    models = genai.list_models()
    
    print(f"Total de modelos encontrados: {len(list(models))}\n")
    
    # Reiniciar el iterador
    models = genai.list_models()
    
    for model in models:
        # Filtrar solo los que soportan generateContent
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ MODELO: {model.name}")
            print(f"   Nombre para usar: {model.name.replace('models/', '')}")
            print(f"   Descripción: {model.display_name}")
            print(f"   Métodos soportados: {', '.join(model.supported_generation_methods)}")
            
            # Mostrar límites si están disponibles
            if hasattr(model, 'input_token_limit'):
                print(f"   Límite de tokens de entrada: {model.input_token_limit:,}")
            if hasattr(model, 'output_token_limit'):
                print(f"   Límite de tokens de salida: {model.output_token_limit:,}")
            
            print()
    
    print("=" * 80)
    print("RECOMENDACIÓN:")
    print("Usa el nombre SIN el prefijo 'models/' en tu código")
    print("Modelos recomendados actuales:")
    print("  - gemini-2.5-flash (más reciente, rápido y eficiente)")
    print("  - gemini-2.5-pro (más potente)")
    print("  - gemini-2.0-flash (estable)")
    print("  - gemini-flash-latest (apunta al más reciente automáticamente)")
    print("Ejemplo: model = genai.GenerativeModel('gemini-2.5-flash')")
    print("=" * 80)
    
except ImportError:
    print("❌ Error: No se pudo importar google.generativeai")
    print("Instala con: pip install google-generativeai")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

