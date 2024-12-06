# Chatbot de WhatsApp con IA

Este proyecto implementa un chatbot para WhatsApp utilizando la API de WhatsApp Business, Flask para el backend, y la IA de OpenAI para el procesamiento de lenguaje natural.

## Arquitectura del Proyecto

El sistema está compuesto por tres servicios principales:

- **WhatsApp Service**: Maneja las peticiones HTTP de WhatsApp y sirve como punto de entrada para los mensajes.
- **OpenAI Service**: Procesa los mensajes usando GPT-4 y mantiene el historial de conversaciones.
- **PostgreSQL**: Almacena datos de conversaciones y configuraciones.


Los servicios están containerizados usando Docker y se comunican entre sí de manera segura.

![Arquitectura WhatsApp AI Chatbot](docs/architecture.png)

### Estructura del Proyecto

```bash
.
├── compose.override.yml     # Configuración de desarrollo
├── compose.yml             # Configuración principal de Docker
├── config/                 # Configuraciones del proyecto
│   └── sheets_config.py    # Configuración de Google Sheets
├── db/                     # Scripts de base de datos
│   └── init.sql           # Inicialización de PostgreSQL
├── ngrok-v3-stable-windows-amd64/  # Cliente ngrok para desarrollo local
│   └── ngrok.exe
├── openai-service/         # Servicio de OpenAI
│   ├── app.py             # Aplicación principal Flask
│   ├── Dockerfile         # Configuración de contenedor
│   ├── langchainService.py # Servicios de LangChain
│   ├── requirements.txt    # Dependencias completas
│   └── shared/            # Código compartido del servicio
│       └── templates/     # Plantillas de prompts
├── shared/                # Código compartido global
│   └── templates/        # Plantillas compartidas
│       └── prompts.py    # Definición de prompts
├── utils/                # Utilidades generales
│   └── sheets_manager.py # Gestor de Google Sheets
└── whatsapp-service/     # Servicio de WhatsApp
    ├── app.py           # Aplicación principal Flask
    ├── Dockerfile       # Configuración de contenedor
    └── handlers/        # Manejadores de eventos
        └── prompt_handler.py # Procesamiento de prompts
```

### Requisitos Previos

Para ejecutar este proyecto necesitas:

- Una cuenta de Google Cloud para el almacenamiento de vectores.
- Una cuenta de desarrollador de Facebook con acceso a la API de WhatsApp Business.
- Acceso a la API de OpenAI.

### Configuración del Entorno

El proyecto utiliza archivos .env separados para cada servicio:

1. WhatsApp Service (.env):
   - PORT
   - WHATSAPP_VERIFY_TOKEN
   - WHATSAPP_ACCESS_TOKEN
   - WHATSAPP_API_URL
   - WHATSAPP_NUMBER_ID
   - OPENAI_SERVICE_URL

2. OpenAI Service (.env):
   - PORT
   - OPENAI_API_KEY
   - DB_HOST
   - DB_NAME
   - DB_USER
   - DB_PASSWORD
   - GOOGLE_SHEETS_CREDENTIALS_FILE
   - GOOGLE_SHEETS_NAME

### Ejecución con Docker

1. Construir y ejecutar los servicios:
```bash
docker-compose up --build
```

2. Solo para desarrollo:
```bash
docker compose -f compose.yml -f compose.override.yml up
```

3. Detener los servicios:
```bash
docker compose down
```

#### Despliegue

- Para desplegar este bot, puedes utilizar servicios como Heroku, AWS, o Google Cloud. Asegúrate de configurar las variables de entorno en tu plataforma de despliegue.
- Una vez que el bot esté en funcionamiento, podrá interactuar con los usuarios a través de WhatsApp, responder preguntas y proporcionar información utilizando la inteligencia artificial de OpenAI.

### CONTRIBUIR

Si tienes ideas, preguntas o deseas discutir sobre las posibilidades de la IA y cómo trabajar juntos para construir soluciones basadas en IAG, no dudes en contactarme:

- GitHub: [https://github.com/albertgilopez](https://github.com/albertgilopez)
- LinkedIn: Albert Gil López: [https://www.linkedin.com/in/albertgilopez/](https://www.linkedin.com/in/albertgilopez/)
- Inteligencia Artificial Generativa (IAG) en español: [https://www.codigollm.es/](https://www.codigollm.es/)

## Build Optimization

The OpenAI service uses a multi-stage Docker build to minimize the final image size. Build times are optimized through:

- Multi-stage builds to separate build dependencies from runtime
- Wheel caching for Python packages
- Minimal base image (python:3.10-slim)
- Separation of dev dependencies

To build for development:
```bash
docker build -t openai-service:dev .
```

For production with minimal image:
```bash
docker build --target production -t openai-service:prod .
```
