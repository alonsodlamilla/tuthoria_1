CREATE TABLE user_states (
    user_id VARCHAR(255) PRIMARY KEY,
    current_state VARCHAR(50) NOT NULL DEFAULT 'INICIO',
    anio VARCHAR(20),
    curso VARCHAR(50),
    seccion VARCHAR(20),
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_states(user_id)
);

CREATE TABLE session_templates (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL,
    template TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar template básico
INSERT INTO session_templates (tipo, template) VALUES 
('SESION_BASE', 'Para {curso} de {anio}, sección {seccion}, genera una sesión que incluya:

1. INICIO (15 minutos):
   - Motivación
   - Saberes previos
   - Conflicto cognitivo

2. DESARROLLO (60 minutos):
   - Actividades de aprendizaje
   - Trabajo individual/grupal
   - Recursos y materiales

3. CIERRE (15 minutos):
   - Evaluación
   - Metacognición
   - Extensión'); 