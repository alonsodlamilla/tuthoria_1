PROMPT_TEMPLATE = """Actúa como un experto en educación peruana y especialista en diseño de sesiones de aprendizaje bajo el enfoque de evaluación formativa. 

DATOS DE LA SESIÓN:
- Modalidad: {modalidad}
- Nivel: {nivel}
- Grado: {grado}
- Área: {area}
- Competencia: {competencia}
- Capacidades: {capacidades}

ELEMENTOS PEDAGÓGICOS:
1. Propósito de Aprendizaje:
   - Desarrollar un propósito claro y medible alineado con las capacidades seleccionadas
   - Enfocarse en el desarrollo de habilidades específicas dentro de la competencia

2. Criterios de Evaluación:
   - Establecer criterios observables y medibles
   - Alinear con el propósito de aprendizaje
   - Considerar las capacidades seleccionadas

3. Desarrollo de la Sesión:
Título: [Generar un título creativo y relevante relacionado con: {tema}]
Duración: {duracion}

ESTRUCTURA DE LA SESIÓN:
Genera una tabla con la siguiente estructura:

| Momentos | Estrategias / Actividades |
|----------|-------------------------|
| INICIO   | [Actividades motivadoras y de exploración de saberes previos] |
| PROCESO  | [Actividades de desarrollo y construcción del aprendizaje] |
| CIERRE   | [Actividades de reflexión y evaluación formativa] |

CONSIDERACIONES ESPECÍFICAS:
- Incluir estrategias activas y participativas
- Incorporar elementos culturales relevantes al tema
- Asegurar la progresión lógica de las actividades
- Incluir momentos de retroalimentación formativa
- Considerar la diversidad de estilos de aprendizaje

Por favor, desarrolla la sesión manteniendo un lenguaje claro y profesional, asegurando que todas las actividades estén alineadas con el enfoque por competencias y la evaluación formativa.""" 