import sqlite3
from datetime import datetime
from typing import Optional, Dict
import threading
from contextlib import contextmanager
import logging
from app.core.config import configuracion

registrador = logging.getLogger(__name__)

class BaseDatos:
    def __init__(self, ruta_db: Optional[str] = None):
        self.ruta_db = ruta_db or configuracion.db_path
        self._bloqueo_local = threading.Lock()
        self._inicializar_db()
    
    def _inicializar_db(self):
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    UNIQUE(name, group_id)
                )
            """)
            self._migrar_esquema_si_necesario(conn)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_name_group ON sessions(name, group_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_group_id ON sessions(group_id)")
            conn.commit()
            registrador.info(f"Base de datos de Identidad inicializada: {self.ruta_db}")

    def _migrar_esquema_si_necesario(self, conn):
        """Migra esquema antiguo UNIQUE(name) → UNIQUE(name, group_id)."""
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sessions'")
        fila = cursor.fetchone()
        if not fila or not fila[0]:
            return
        if "UNIQUE(name, group_id)" in fila[0]:
            return

        registrador.info("Migrando tabla sessions a unicidad por (name, group_id)")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions_new (
                session_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                group_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                UNIQUE(name, group_id)
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO sessions_new (session_id, name, group_id, created_at, expires_at)
            SELECT session_id, name, group_id, created_at, expires_at FROM sessions
        """)
        cursor.execute("DROP TABLE sessions")
        cursor.execute("ALTER TABLE sessions_new RENAME TO sessions")
        conn.commit()
    
    @contextmanager
    def _obtener_conexion(self):
        conn = sqlite3.connect(self.ruta_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def crear_sesion(self, id_sesion: str, nombre: str, id_grupo: str, fecha_expiracion: datetime) -> bool:
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
                return False
    
    def obtener_sesion(self, id_sesion: str) -> Optional[Dict]:
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
    
    def obtener_sesion_por_nombre_y_grupo(self, nombre: str, id_grupo: str) -> Optional[Dict]:
        ahora = datetime.utcnow().isoformat()
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, name, group_id, created_at, expires_at
                FROM sessions
                WHERE name = ? AND group_id = ? AND expires_at > ?
            """, (nombre, id_grupo, ahora))
            fila = cursor.fetchone()
            if fila:
                return dict(fila)
            return None
    
    def eliminar_sesion(self, id_sesion: str) -> bool:
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (id_sesion,))
            conn.commit()
            return cursor.rowcount > 0

    def limpiar_sesiones_expiradas(self) -> int:
        ahora = datetime.utcnow().isoformat()
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE expires_at <= ?", (ahora,))
            eliminadas = cursor.rowcount
            conn.commit()
            return eliminadas

    def obtener_cantidad_sesiones_activas(self) -> int:
        ahora = datetime.utcnow().isoformat()
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > ?", (ahora,))
            return cursor.fetchone()[0]

base_datos = BaseDatos()
