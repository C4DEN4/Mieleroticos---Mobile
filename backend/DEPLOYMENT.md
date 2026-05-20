# Guía de Despliegue en AWS EC2 (Ubuntu) - Classroom Hub Backend

Esta guía describe el paso a paso detallado para desplegar la arquitectura distribuida del backend de Classroom Hub en una instancia EC2 de AWS con **Ubuntu Server** mediante la terminal (CLI).

---

## 1. Configuración de la Instancia AWS EC2

### Crear Instancia
1. Inicia sesión en la consola de AWS.
2. Ve a **EC2** -> **Instances** -> **Launch Instance**.
3. Selecciona un nombre para tu máquina (ej. `Classroom-Hub-Backend`).
4. **OS (Operating System)**: Selecciona **Ubuntu Server 22.04 LTS** o **Ubuntu Server 24.04 LTS** (64-bit x86).
5. **Instance Type**: `t2.micro` o `t3.micro` (dentro de la capa gratuita).
6. **Key Pair (SSH)**: Crea o asocia una llave `.pem` para acceder por consola.

### Configurar el Security Group (Reglas de Entrada)
Es **indispensable** abrir los siguientes puertos en el Security Group asociado para permitir que los clientes y tú se conecten:

| Tipo | Puerto | Origen | Descripción |
|------|--------|--------|-------------|
| **SSH** | `22` | Mi IP / Cualquiera (`0.0.0.0/0`) | Acceso remoto por consola |
| **HTTP** | `80` | Cualquiera (`0.0.0.0/0`) | Requerido por Nginx y Certbot (SSL) |
| **HTTPS** | `443` | Cualquiera (`0.0.0.0/0`) | Requerido para la conexión segura `wss://` |
| **Custom TCP** | `8000` | Cualquiera (`0.0.0.0/0`) | Acceso directo al BFF (opcional para pruebas) |
| **Custom TCP** | `8001` | Cualquiera (`0.0.0.0/0`) | Acceso al microservicio de Identidad (opcional para pruebas) |
| **Custom TCP** | `8002` | Cualquiera (`0.0.0.0/0`) | Acceso al microservicio de Grupos (opcional para pruebas) |

---

## 2. Acceso por Consola e Instalación de Dependencias

Conéctate a tu máquina EC2 mediante tu terminal SSH:
```bash
ssh -i "tu-llave.pem" ubuntu@IP_PUBLICA_DE_TU_EC2
```

Una vez dentro, ejecuta los siguientes comandos para actualizar el sistema e instalar Docker y Docker Compose:

### Actualizar paquetes
```bash
sudo apt update && sudo apt upgrade -y
```

### Instalar Docker
```bash
# Agregar la llave oficial de Docker
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Agregar el repositorio de Docker a las fuentes de Apt
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine y Docker Compose CLI
sudo apt update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Añadir tu usuario al grupo docker para no usar 'sudo' en cada comando
sudo usermod -aG docker $USER
```
*Nota: Cierra la sesión SSH (`exit`) y vuelve a conectarte para que aplique el cambio de grupo sin sudo.*

---

## 3. Subir el Código y Desplegar

### Copiar el código a la EC2
Puedes clonar tu repositorio directamente desde la terminal de la EC2, o bien usar `scp` para subir la carpeta `backend/` desde tu máquina local:
```bash
# Ejemplo usando scp desde tu terminal local
scp -i "tu-llave.pem" -r ./backend ubuntu@IP_PUBLICA_DE_TU_EC2:/home/ubuntu/
```

### Levantar los contenedores
En la terminal de la EC2, navega a la carpeta subida e inicia la orquestación:
```bash
cd /home/ubuntu/backend

# Construir e iniciar los microservicios en segundo plano
docker compose up -d --build
```

### Verificar que estén corriendo
```bash
docker compose ps
```
Deberías ver 3 contenedores activos:
- `bff-service` en el puerto `8000`
- `identity-service` en el puerto `8001`
- `groups-service` en el puerto `8002`

---

## 4. Pruebas y Validación (Demostración al Profesor)

### Pruebas de Endpoints de Salud (Health Checks)
Puedes verificar que todo funcione consultando el BFF, el cual mapeará e informará el estado de los microservicios de Identidad y Grupos:
```bash
curl http://localhost:8000/health
```
**Respuesta exitosa:**
```json
{
  "estado": "saludable",
  "nombre_aplicacion": "Classroom Hub BFF",
  "conexiones_activas": 0,
  "grupos_activos": 0,
  "servicios_internos": {
    "identity_service": "saludable",
    "groups_service": "saludable"
  }
}
```

---

## 5. Ingeniería del Caos (Prueba de Resiliencia)

Durante la sustentación, el profesor inyectará fallos en los microservicios centrales. Nuestra arquitectura está preparada para resistir esto de manera autónoma:

### Escenario A: Caída del Microservicio de Identidad (Prueba oral)
Si el profesor te pide apagar el servicio de Identidad para verificar la resiliencia:
```bash
docker compose stop identity-service
```
1. **Lo que sucede**:
   - Si consultas `curl http://localhost:8000/health`, la sección `"identity_service"` mostrará `"caído / no disponible"` y el estado general será `"degradado"`.
   - **Los estudiantes que ya estaban conectados por WebSocket en la clase podrán seguir enviando señales y recibiendo notificaciones sin interrupciones**, ya que su canal WebSocket está en la memoria del BFF.
   - Las nuevas conexiones WebSocket o peticiones de creación de sesión fallarán gracefully respondiendo un error amigable en lugar de colapsar.
2. **Restaurar el servicio**:
   - `docker compose start identity-service` (el sistema vuelve a estar 100% saludable de forma automática).

### Escenario B: Caída del Microservicio de Grupos (Idempotencia)
Si se apaga el microservicio de Grupos:
```bash
docker compose stop groups-service
```
1. **Lo que sucede**:
   - El control estricto de eventos duplicados (offline synchronization) pasará a modo seguro de bypass.
   - El BFF **seguirá retransmitiendo las señales de los estudiantes instantáneamente**, asegurando que la clase no pierda conectividad en tiempo real (degradación grácil del servicio de idempotencia).

---

## 6. Configuración de SSL / TLS (WSS para Móviles en Producción)

Los dispositivos móviles modernos (iOS y Android) y los navegadores web **bloquean** conexiones WebSocket inseguras (`ws://`) desde aplicaciones cargadas sobre entornos seguros. Es mandatorio levantar un proxy inverso con SSL (`wss://`).

### Instalar Nginx y Certbot en Ubuntu
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Configurar Nginx
Crea un archivo de configuración para tu dominio en Nginx:
```bash
sudo nano /etc/nginx/sites-available/classroom_hub
```

Pega el siguiente contenido (reemplaza `tu-dominio.com` por el dominio o subdominio asignado a tu EC2, por ejemplo, uno gratuito de DuckDNS o similar):
```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Habilita la configuración y reinicia Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/classroom_hub /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Obtener Certificado SSL Gratuito (Let's Encrypt)
Ejecuta Certbot para automatizar la instalación de SSL en tu servidor:
```bash
sudo certbot --nginx -d tu-dominio.com
```
*Sigue las instrucciones de pantalla (ingresa tu email y acepta los términos).*

¡Listo! A partir de este momento, tu backend estará escuchando conexiones seguras en:
- API REST: `https://tu-dominio.com`
- WebSocket: `wss://tu-dominio.com/ws`
