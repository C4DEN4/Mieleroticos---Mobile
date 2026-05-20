# Usar imagen base de Python slim
FROM python:3.13-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto 8000
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:aplicacion", "--host", "0.0.0.0", "--port", "8000"]
