import sqlite3
from datetime import datetime
from typing import Optional
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
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processed_events'")
            existe_tabla = cursor.fetchone() is not None
            if existe_tabla:
                cursor.execute("PRAGMA table_info(processed_events)")
                columnas = {fila[1] for fila in cursor.fetchall()}
                if "group_id" not in columnas:
                    cursor.execute("DROP TABLE IF EXISTS processed_events")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    group_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    PRIMARY KEY (group_id, event_id)
                )
            """)
            conn.commit()
            registrador.info(f"Base de datos de Grupos inicializada: {self.ruta_db}")
    
    @contextmanager
    def _obtener_conexion(self):
        conn = sqlite3.connect(self.ruta_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def registrar_evento_procesado(self, id_grupo: str, id_evento: str) -> bool:
        ahora = datetime.utcnow().isoformat()
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO processed_events (group_id, event_id, processed_at)
                    VALUES (?, ?, ?)
                """, (id_grupo, id_evento, ahora))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def evento_fue_procesado(self, id_grupo: str, id_evento: str) -> bool:
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_events WHERE group_id = ? AND event_id = ?",
                (id_grupo, id_evento)
            )
            return cursor.fetchone() is not None
    
    def reconocer_evento(self, id_grupo: str, id_evento: str) -> bool:
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM processed_events WHERE group_id = ? AND event_id = ?",
                (id_grupo, id_evento)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def limpiar_eventos_antiguos(self, horas: int = 24) -> int:
        from datetime import timedelta
        limite = (datetime.utcnow() - timedelta(hours=horas)).isoformat()
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM processed_events WHERE processed_at < ?", (limite,))
            eliminados = cursor.rowcount
            conn.commit()
            return eliminados
    
    def obtener_cantidad_eventos_procesados(self) -> int:
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_events")
            return cursor.fetchone()[0]

base_datos = BaseDatos()
