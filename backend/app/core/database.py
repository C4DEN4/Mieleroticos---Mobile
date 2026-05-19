import sqlite3
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import threading
from contextlib import contextmanager
import logging

registrador = logging.getLogger(__name__)


class BaseDatos:
    """
    Gestor de base de datos SQLite para persistencia de sesiones y eventos procesados.
    
    Implementa tolerancia a fallos mediante persistencia en disco.
    """
    
    def __init__(self, ruta_db: str = "classroom_hub.db"):
        self.ruta_db = ruta_db
        self._bloqueo_local = threading.Lock()
        self._inicializar_db()
    
    def _inicializar_db(self):
        """Inicializa la base de datos y crea las tablas necesarias."""
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Tabla de sesiones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    UNIQUE(name)
                )
            """)
            
            # Tabla de eventos procesados (idempotencia)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    event_id TEXT PRIMARY KEY,
                    processed_at TEXT NOT NULL
                )
            """)
            
            # Índices para mejor rendimiento
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at 
                ON sessions(expires_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_name 
                ON sessions(name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_group_id 
                ON sessions(group_id)
            """)
            
            conn.commit()
            registrador.info(f"Base de datos inicializada: {self.ruta_db}")
    
    @contextmanager
    def _obtener_conexion(self):
        """Context manager para obtener conexión a la base de datos."""
        conn = sqlite3.connect(self.ruta_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # Métodos para sesiones
    def crear_sesion(self, id_sesion: str, nombre: str, id_grupo: str, 
                     fecha_expiracion: datetime) -> bool:
        """
        Crea una nueva sesión en la base de datos.
        
        Retorna True si se creó exitosamente, False si el nombre ya existe.
        """
        ahora = datetime.utcnow().isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO sessions (session_id, name, group_id, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (id_sesion, nombre, id_grupo, ahora, fecha_expiracion.isoformat()))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # El nombre ya existe
                return False
    
    def obtener_sesion(self, id_sesion: str) -> Optional[Dict]:
        """
        Obtiene una sesión por ID si no está expirada.
        
        Retorna None si no existe o está expirada.
        """
        ahora = datetime.utcnow().isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, name, group_id, created_at, expires_at
                FROM sessions
                WHERE session_id = ? AND expires_at > ?
            """, (id_sesion, ahora))
            
            fila = cursor.fetchone()
            if fila:
                return dict(fila)
            return None
    
    def obtener_sesion_por_nombre(self, nombre: str) -> Optional[Dict]:
        """
        Obtiene una sesión por nombre si no está expirada.
        
        Retorna None si no existe o está expirada.
        """
        ahora = datetime.utcnow().isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, name, group_id, created_at, expires_at
                FROM sessions
                WHERE name = ? AND expires_at > ?
            """, (nombre, ahora))
            
            fila = cursor.fetchone()
            if fila:
                return dict(fila)
            return None
    
    def eliminar_sesion(self, id_sesion: str) -> bool:
        """Elimina una sesión por ID."""
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (id_sesion,))
            conn.commit()
            return cursor.rowcount > 0
    
    def limpiar_sesiones_expiradas(self) -> int:
        """
        Elimina todas las sesiones expiradas.
        
        Retorna el número de sesiones eliminadas.
        """
        ahora = datetime.utcnow().isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE expires_at <= ?", (ahora,))
            eliminadas = cursor.rowcount
            conn.commit()
            return eliminadas
    
    def obtener_cantidad_sesiones_activas(self) -> int:
        """Obtiene el conteo de sesiones activas (no expiradas)."""
        ahora = datetime.utcnow().isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sessions WHERE expires_at > ?
            """, (ahora,))
            return cursor.fetchone()[0]
    
    def obtener_sesiones_por_grupo(self, id_grupo: str) -> List[Dict]:
        """Obtiene todas las sesiones activas de un grupo."""
        ahora = datetime.utcnow().isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, name, group_id, created_at, expires_at
                FROM sessions
                WHERE group_id = ? AND expires_at > ?
            """, (id_grupo, ahora))
            
            return [dict(fila) for fila in cursor.fetchall()]
    
    # Métodos para idempotencia de eventos
    def registrar_evento_procesado(self, id_evento: str) -> bool:
        """
        Registra un evento como procesado.
        
        Retorna True si se registró exitosamente, False si ya existía.
        """
        ahora = datetime.utcnow().isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO processed_events (event_id, processed_at)
                    VALUES (?, ?)
                """, (id_evento, ahora))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # El evento ya existe
                return False
    
    def evento_fue_procesado(self, id_evento: str) -> bool:
        """
        Verifica si un evento ya fue procesado.
        
        Retorna True si fue procesado, False de lo contrario.
        """
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM processed_events WHERE event_id = ?
            """, (id_evento,))
            return cursor.fetchone() is not None
    
    def reconocer_evento(self, id_evento: str) -> bool:
        """
        Elimina un evento de la tabla de procesados después de ser reconocido.
        
        Retorna True si se eliminó, False si no existía.
        """
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM processed_events WHERE event_id = ?", (id_evento,))
            conn.commit()
            return cursor.rowcount > 0
    
    def limpiar_eventos_antiguos(self, horas: int = 24) -> int:
        """
        Limpia eventos procesados más antiguos que el número de horas especificado.
        
        Retorna el número de eventos eliminados.
        """
        from datetime import timedelta
        limite = (datetime.utcnow() - timedelta(hours=horas)).isoformat()
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM processed_events WHERE processed_at < ?
            """, (limite,))
            eliminados = cursor.rowcount
            conn.commit()
            return eliminados
    
    def obtener_cantidad_eventos_procesados(self) -> int:
        """Obtiene el conteo de eventos procesados en caché."""
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_events")
            return cursor.fetchone()[0]


# Instancia global de la base de datos
base_datos = BaseDatos()
