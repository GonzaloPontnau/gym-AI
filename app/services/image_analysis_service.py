import os
import base64
from io import BytesIO
import google.generativeai as genai
from dotenv import load_dotenv

# Intentar importar PIL, si no está disponible, definir un flag
PIL_AVAILABLE = False
try:
    from PIL import Image
    PIL_AVAILABLE = True
    print("✅ PIL (Pillow) está disponible - Funcionalidad de análisis de imágenes activada")
except ImportError:
    print("⚠️ PIL (Pillow) no está instalado - Funcionalidad de análisis de imágenes desactivada")

# Cargar variables de entorno
load_dotenv()

# Verificar si la API de Gemini está configurada
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY no está configurada - Funcionalidad de IA limitada")
else:
    # Configurar la API de Gemini con la clave API
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ API de Gemini configurada correctamente")
        # Definir el modelo a utilizar (gemini-1.5-flash es multimodal)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"❌ Error al configurar la API de Gemini: {str(e)}")

class GeminiImageAnalyzer:
    """Servicio para analizar imágenes de ejercicios usando la API de Gemini"""
    
    async def analyze_exercise_image(self, image_data, exercise_name=None):
        """
        Analiza una imagen de un ejercicio y proporciona retroalimentación sobre la postura
        
        Args:
            image_data: La imagen en formato bytes o base64
            exercise_name: Nombre del ejercicio (opcional)
        
        Returns:
            str: Análisis y feedback sobre la postura y técnica
        """
        # Verificar si PIL está disponible
        if not PIL_AVAILABLE:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada debido a que la biblioteca PIL (Pillow) no está instalada en el servidor."
        
        # Verificar si la API de Gemini está configurada
        if not GEMINI_API_KEY:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada porque no se ha configurado la API de Gemini."
        
        try:
            # Mejorar la validación de imágenes para mitigar vulnerabilidades
            image = None
            
            # Convertir datos de imagen si es necesario
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                # Definir un límite máximo para tamaño de imagen (10MB)
                MAX_IMAGE_SIZE = 10 * 1024 * 1024
                
                # Extraer datos base64
                try:
                    image_data = image_data.split(',')[1]
                    image_bytes = base64.b64decode(image_data)
                    
                    # Verificar tamaño
                    if len(image_bytes) > MAX_IMAGE_SIZE:
                        return "La imagen es demasiado grande. Por favor, utiliza una imagen más pequeña (max. 10MB)."
                    
                    # Validar que sea una imagen real antes de procesarla
                    image = Image.open(BytesIO(image_bytes))
                    image.verify()  # Verificar que es una imagen válida
                    
                    # Reabrir después de verify() ya que verify cierra el archivo
                    image = Image.open(BytesIO(image_bytes))
                except Exception as e:
                    print(f"Error al validar imagen: {str(e)}")
                    return "No se pudo procesar la imagen. El formato no es válido o está corrupta."
                    
            elif isinstance(image_data, bytes):
                # Verificar tamaño
                MAX_IMAGE_SIZE = 10 * 1024 * 1024
                if len(image_data) > MAX_IMAGE_SIZE:
                    return "La imagen es demasiado grande. Por favor, utiliza una imagen más pequeña (max. 10MB)."
                
                try:
                    # Validar que sea una imagen real
                    image = Image.open(BytesIO(image_data))
                    image.verify()
                    # Reabrir después de verify()
                    image = Image.open(BytesIO(image_data))
                except Exception as e:
                    print(f"Error al validar imagen: {str(e)}")
                    return "No se pudo procesar la imagen. El formato no es válido o está corrupta."
            else:
                try:
                    # Intentar abrir como flujo de bytes
                    image = Image.open(BytesIO(image_data))
                    image.verify()
                    # Reabrir después de verify()
                    image = Image.open(BytesIO(image_data))
                except Exception as e:
                    print(f"Error al validar imagen: {str(e)}")
                    return "Formato de imagen no compatible. Por favor, intenta con otro formato."
            
            # Asegurar que tenemos una imagen válida antes de continuar
            if not image:
                return "No se pudo procesar la imagen. Por favor, intenta con otro formato."
            
            # Construir el prompt según si tenemos el nombre del ejercicio o no
            if exercise_name:
                prompt = f"""
                Analiza esta imagen donde la persona está realizando el ejercicio: {exercise_name}.
                
                Por favor, proporciona:
                1. Una evaluación de su postura y técnica
                2. Puntos específicos de mejora
                3. Consejos para mejorar la forma del ejercicio
                4. Posibles riesgos de lesión basados en la técnica mostrada
                
                Responde en español de forma clara y concisa.
                """
            else:
                prompt = """
                Analiza esta imagen de una persona haciendo ejercicio.
                
                Por favor:
                1. Identifica qué ejercicio está realizando
                2. Evalúa su postura y técnica
                3. Proporciona consejos específicos para mejorar
                4. Menciona los beneficios del ejercicio y músculos trabajados
                
                Responde en español de forma clara y concisa.
                """
            
            # Generar el análisis con Gemini
            response = model.generate_content([prompt, image])
            
            # Devolver el resultado
            return response.text.strip()
            
        except Exception as e:
            print(f"Error al analizar la imagen con Gemini: {str(e)}")
            return "No se pudo analizar la imagen. Por favor, inténtalo de nuevo con una imagen más clara o desde otro ángulo."
    
    async def suggest_exercise_variations(self, image_data, difficulty_level=None):
        """
        Analiza una imagen de un ejercicio y sugiere variaciones
        
        Args:
            image_data: La imagen en formato bytes o base64
            difficulty_level: Nivel de dificultad deseado (más fácil, similar, más difícil)
        
        Returns:
            str: Sugerencias de variaciones del ejercicio
        """
        # Verificaciones iniciales
        if not PIL_AVAILABLE:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada debido a que la biblioteca PIL (Pillow) no está instalada en el servidor."
        
        if not GEMINI_API_KEY:
            return "Lo siento, la funcionalidad de análisis de imágenes está deshabilitada porque no se ha configurado la API de Gemini."
        
        try:
            # Convertir datos de imagen
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(BytesIO(image_bytes))
            else:
                image = Image.open(BytesIO(image_data))
            
            # Construir el prompt según el nivel de dificultad
            if difficulty_level:
                prompt = f"""
                Observa esta imagen de ejercicio y sugiere 3-4 variaciones {difficulty_level} del mismo.
                
                Para cada variación, incluye:
                - Nombre del ejercicio
                - Breve descripción de cómo realizarlo
                - Músculos principales trabajados
                - Nivel de dificultad comparado con el ejercicio original
                
                Responde en español de forma clara y concisa.
                """
            else:
                prompt = """
                Observa esta imagen de ejercicio y sugiere 4-5 variaciones alternativas que trabajen los mismos grupos musculares.
                
                Para cada variación, incluye:
                - Nombre del ejercicio
                - Breve descripción de cómo realizarlo
                - Equipo necesario (si aplica)
                - Si es más fácil o más difícil que el ejercicio mostrado
                
                Responde en español de forma clara y concisa.
                """
            
            # Generar las sugerencias con Gemini
            response = model.generate_content([prompt, image])
            
            # Devolver el resultado
            return response.text.strip()
            
        except Exception as e:
            print(f"Error al generar variaciones con Gemini: {str(e)}")
            return "No se pudieron generar variaciones. Por favor, inténtalo de nuevo con una imagen más clara."
