# GymAI - Tu personal TrAIner

[![FastAPI](https://img.shields.io/badge/docs-FastAPI-white?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/docs-Python-blue?logo=python)](https://docs.python.org/3/)
[![Gemini](https://img.shields.io/badge/API-Google_Gemini-green?logo=google)](https://ai.google.dev/)

## Demo

### Dashboard Principal
![demo-dashboard]()

### Generación de Rutinas
![demo-rutinas]()

### Análisis de Posturas
![demo-analisis]()

### Chat en Tiempo Real
![demo-chat]()

## Descripción

GymAI es una aplicación web que utiliza inteligencia artificial (Google Gemini) para generar y personalizar rutinas de entrenamiento adaptadas a las necesidades específicas de cada usuario. Con un enfoque en la experiencia del usuario, permite modificar rutinas en tiempo real mediante un chat interactivo y ofrece análisis de posturas a través del procesamiento de imágenes.

> [!TIP]
> Esta aplicación permite combinar ejercicios según tus objetivos específicos, equipo disponible y nivel de condición física.

---

## Características Principales

- **Generación de Rutinas**: Creación de planes de entrenamiento personalizados según objetivos y nivel
- **Chat Interactivo**: Comunicación en tiempo real para modificar rutinas sobre la marcha
- **Análisis de Imágenes**: Evaluación y corrección de posturas en ejercicios
- **Seguimiento de Progreso**: Monitoreo de avances y logros
- **Diseño Adaptable**: Interfaz responsive para todos los dispositivos
- **Recomendaciones Inteligentes**: Sugerencias basadas en el rendimiento y preferencias
- **Almacenamiento de Rutinas**: Historial completo de entrenamientos realizados
- **Exportación de Datos**: Posibilidad de descargar rutinas en formato PDF

---

## Tecnologías Utilizadas

- **Backend**: 
   - FastAPI (Python 3.9+)
   - WebSockets para comunicación en tiempo real
   - SQLite/PostgreSQL para almacenamiento de datos
   
- **Frontend**: 
   - HTML5, CSS3, JavaScript
   - Bootstrap 5 para interfaz responsive
   - HTMX para interactividad sin complicaciones
   
- **Inteligencia Artificial**:
   - Google Gemini API para generación de rutinas
   - Análisis de imágenes para corrección de posturas
   
- **DevOps**:
   - Render para despliegue automatizado
   
- **Comunicación en Tiempo Real**:
   - WebSockets para chat interactivo
   - Notificaciones push en tiempo real
   - Actualizaciones instantáneas de rutinas

> [!NOTE]
> Este proyecto implementa una arquitectura moderna basada en API REST con comunicación en tiempo real vía WebSockets para una experiencia fluida.

---

## Estructura del Proyecto

```
gym-AI/
│
├── app/                    # Aplicación principal
│   ├── db/                 # Configuración y modelos de base de datos
│   ├── models/             # Modelos de datos
│   ├── services/           # Servicios de IA y generación de rutinas
│   ├── websocket/          # Gestión de comunicación en tiempo real
│   ├── main.py             # Punto de entrada principal
│   └── sqlite_helper.py    # Utilidades para manejo de SQLite
│
├── static/                 # Archivos estáticos
│   ├── css/                # Estilos
│
├── templates/              # Plantillas HTML
│   ├── base.html           # Plantilla base
│   ├── dashboard.html      # Dashboard principal
│   └── routines_list.html  # Lista de rutinas
│
├── scripts/                # Scripts de utilidad
├── requirements.txt        # Dependencias del proyecto
├── render.yaml             # Configuración para despliegue en Render
└── README.md               # Este archivo
```


### Motor de Análisis de Imágenes

El sistema puede analizar imágenes de ejercicios para:
- Detectar errores comunes en la postura
- Proporcionar correcciones específicas
- Registrar progreso visual a lo largo del tiempo

---

## Lecciones Aprendidas y Desafíos

- Integración efectiva de APIs de IA con sistemas web en tiempo real
- Optimización de respuestas de modelo para reducir latencia
- Diseño de interfaces de usuario intuitivas para interacción con IA

Algunos de los desafíos enfrentados incluyen:

- Gestión eficiente de conexiones WebSocket a escala
- Personalización de respuestas de IA según el contexto del usuario
- Configuración óptima para el despliegue de archivos estáticos en Render


---

## 👨‍💻 Desarrollado por

**Ing. Pontnau, Gonzalo Martín**

💼 [LinkedIn](https://linkedin.com/in/gonzalopontnau)
📧 [Email](mailto:gonzalopontnau@gmail.com)
💻 [Portfolio](https://gonzalopontnau.github.io/)

---