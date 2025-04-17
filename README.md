# Gym-AI - Gestor Inteligente de Rutinas con IA

## 1. Visión General

### 1.1 Concepto
GymAI es una aplicación web para la creación y gestión de rutinas de entrenamiento personalizadas mediante inteligencia artificial. Su flujo único de dos fases (conversación inicial seguida de dashboard interactivo) permite a los usuarios crear y modificar rutinas de forma intuitiva a través de lenguaje natural.

### 1.2 Propuesta de Valor
- **Personalización mediante IA**: Creación de rutinas adaptadas a objetivos, nivel y equipamiento disponible
- **Interfaz conversacional**: Interacción natural mediante chat para crear y modificar rutinas
- **Dashboard visual**: Visualización clara de la rutina con modificación en tiempo real
- **Persistencia contextual**: Conservación del historial de conversación para referencias y ajustes futuros

## 2. Stack Tecnológico
| Capa | Tecnologías |
|------|-------------|
| **Backend** | Python (FastAPI), SQLAlchemy ORM, Pydantic, JWT, WebSockets |
| **Frontend** | Jinja2 (plantillas HTML), HTMX, JavaScript, CSS (Tailwind o Bootstrap) |
| **IA/ML** | Google Gemini API (gemini-2.0-flash), Prompt Engineering |
| **Base de Datos** | PostgreSQL |

## 3. Funcionalidades Principales

1. **Creación Inicial (Chat)**
   - Pantalla de chat minimalista
   - IA guía al usuario con preguntas estructuradas:
     - "¿Cuáles son tus objetivos? (aumentar masa, definición, etc.)"
     - "¿Qué equipamiento tienes disponible?"
     - "¿Cuántos días puedes entrenar a la semana?"
   - Construcción progresiva de la rutina durante la conversación
   - Botón "Finalizar y ver rutina" tras confirmación

2. **Dashboard Principal**
   - Visualización semanal de la rutina (3 dias)
   - Cada día muestra ejercicios, series, repeticiones
   - Chat lateral persistente para modificaciones
   - Posibilidad de guardar versiones de la rutina
   - Opción para imprimir/exportar PDF

3. **Chat Lateral para Modificaciones**
   - Historial de conversación mantenido
   - Capacidad para solicitar cambios específicos:
     - "Reemplaza press de banca por flexiones el lunes"
     - "Agrega más ejercicios para piernas el viernes"
     - "Quiero enfocarme más en cardio esta semana"
   - Visualización de los cambios en tiempo real en el dashboard

## 5. Interfaces de Usuario

### 5.1 Pantalla de Chat Inicial
- Diseño minimalista centrado en la conversación
- Indicadores visuales del progreso de creación
- Ejemplos de preguntas sugeridas
- Visualización previa simplificada de la rutina en construcción

### 5.2 Dashboard Principal
- Vista semanal con días organizados horizontalmente
- Tarjetas por ejercicio con información detallada
- Códigos de color según tipo de ejercicio (cardio, fuerza, etc.)
- Panel lateral de chat persistente (30% del ancho)
- Barra superior con acciones (guardar, exportar, compartir)


## 4. AI Features

### 4.1 Tipos de Prompts
- **Prompt de Creación**: Genera rutina completa basada en información inicial
- **Prompt de Modificación**: Modifica aspectos específicos preservando el resto
- **Prompt Explicativo**: Proporciona explicación sobre ejercicios o decisiones
- **Prompt de Sugerencias**: Recomienda mejoras basadas en progresos/feedback

### 4.2 Estructura de Datos de Respuesta
- Rutina completa en formato JSON
- Explicaciones textuales para el usuario
- Metadatos para seguimiento de cambios

### 4.3 Estrategias de Prompt Engineering
- Instrucciones claras sobre formato requerido
- Contexto completo de la rutina actual
- Especificación de restricciones (equipamiento, lesiones)
- Manejo de casos extremos y validaciones
