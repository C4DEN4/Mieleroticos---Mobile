import { obtenerUrlWebSocket } from '../config/api';

const WS_OPEN = 1;
const WS_CONNECTING = 0;
const WS_CLOSING = 2;
const WS_CLOSED = 3;

class ServicioConexion {
  constructor() {
    this.socket = null;
    this.callbacks = {};
    this.urlServidor = 'http://localhost:8000';
    this.intervaloPingPong = null;
    this.timeoutReconexion = null;
    this.intentosReconexion = 0;
    this.maxIntentosReconexion = 6;
    this._manejadorMensaje = null;
    this._desconexionIntencional = false;
    this._reemplazandoSocket = false;
    this._conexionEnProgreso = false;
    this._reconexionProgramada = false;
    this._sesionActiva = null;
    this._ultimaUrlWs = '';
  }

  obtenerUltimaUrlWs() {
    return this._ultimaUrlWs;
  }

  establecerURL(url) {
    this.urlServidor = url;
  }

  _extraerMensajeError(cuerpo) {
    if (!cuerpo) {
      return 'Error desconocido';
    }
    if (typeof cuerpo === 'string') {
      return cuerpo;
    }
    if (cuerpo.mensaje) {
      return cuerpo.mensaje;
    }
    if (cuerpo.detail) {
      if (typeof cuerpo.detail === 'string') {
        return cuerpo.detail;
      }
      return cuerpo.detail.mensaje || cuerpo.detail.message || JSON.stringify(cuerpo.detail);
    }
    return cuerpo.message || 'Error en la peticion';
  }

  async verificarSesionActiva(idSesion) {
    try {
      const respuesta = await fetch(`${this.urlServidor}/api/v1/sessions/${idSesion}`);
      return respuesta.ok;
    } catch {
      return false;
    }
  }

  async crearSesion(nombre, idGrupo) {
    try {
      const respuesta = await fetch(`${this.urlServidor}/api/v1/sessions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: nombre, group_id: idGrupo }),
      });

      const cuerpo = await respuesta.json().catch(() => ({}));
      if (!respuesta.ok) {
        throw new Error(this._extraerMensajeError(cuerpo));
      }
      return cuerpo;
    } catch (error) {
      console.error('Error al crear sesion:', error);
      throw error;
    }
  }

  async eliminarSesion(idSesion) {
    try {
      const respuesta = await fetch(`${this.urlServidor}/api/v1/sessions/${idSesion}`, {
        method: 'DELETE',
      });
      if (!respuesta.ok && respuesta.status !== 204) {
        throw new Error('Error al eliminar sesion');
      }
      return true;
    } catch (error) {
      console.error('Error al eliminar sesion:', error);
      throw error;
    }
  }

  async obtenerMiembrosGrupo(idGrupo) {
    try {
      const respuesta = await fetch(`${this.urlServidor}/api/v1/groups/${idGrupo}/connections`);
      if (!respuesta.ok) {
        throw new Error('Error al obtener miembros del grupo');
      }
      const datos = await respuesta.json();
      return datos.names || [];
    } catch (error) {
      console.error('Error al obtener miembros del grupo:', error);
      throw error;
    }
  }

  _procesarMensajeEntrante(datos) {
    if (datos.type === 'notification' && this.callbacks.onNotificacion) {
      this.callbacks.onNotificacion(datos);
    } else if (datos.type === 'ack' && this.callbacks.onAck) {
      this.callbacks.onAck(datos);
    } else if (datos.type === 'error' && this.callbacks.onError) {
      this.callbacks.onError(datos);
    }
  }

  _limpiarTimeoutReconexion() {
    if (this.timeoutReconexion) {
      clearTimeout(this.timeoutReconexion);
      this.timeoutReconexion = null;
    }
  }

  _mismaSesion(idSesion, idGrupo, nombre) {
    return (
      this._sesionActiva?.idSesion === idSesion &&
      this._sesionActiva?.idGrupo === idGrupo &&
      this._sesionActiva?.nombre === nombre
    );
  }

  _programarReconexion() {
    if (
      this._desconexionIntencional ||
      !this._sesionActiva ||
      this._reconexionProgramada ||
      this._conexionEnProgreso
    ) {
      return;
    }

    if (this.intentosReconexion >= this.maxIntentosReconexion) {
      if (this.callbacks.onReconexionFallida) {
        this.callbacks.onReconexionFallida();
      }
      return;
    }

    this.intentosReconexion += 1;
    this._reconexionProgramada = true;
    const delayMs = Math.min(2000 * this.intentosReconexion, 10000);

    if (this.callbacks.onReconectando) {
      this.callbacks.onReconectando(this.intentosReconexion);
    }

    this.timeoutReconexion = setTimeout(() => {
      this._reconexionProgramada = false;
      if (!this._sesionActiva || this._desconexionIntencional) {
        return;
      }
      const { idSesion, idGrupo, nombre, callbacks } = this._sesionActiva;
      this._abrirWebSocket(idSesion, idGrupo, nombre, callbacks);
    }, delayMs);
  }

  iniciarConexionWebSocket(idSesion, idGrupo, nombre, callbacks) {
    if (
      this._mismaSesion(idSesion, idGrupo, nombre) &&
      (this.estaConectado() || this.socket?.readyState === WS_CONNECTING)
    ) {
      this.callbacks = callbacks;
      this._sesionActiva.callbacks = callbacks;
      return;
    }

    this.desconectarWebSocket(true);
    this.callbacks = callbacks;
    this._sesionActiva = { idSesion, idGrupo, nombre, callbacks };
    this._desconexionIntencional = false;
    this.intentosReconexion = 0;
    this._abrirWebSocket(idSesion, idGrupo, nombre, callbacks);
  }

  _abrirWebSocket(idSesion, idGrupo, nombre, callbacks) {
    if (this._conexionEnProgreso) {
      return;
    }

    this._conexionEnProgreso = true;
    this.detenerPingPong();
    this.callbacks = callbacks;

    if (this.socket) {
      this._reemplazandoSocket = true;
      this.socket.onopen = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;
      if (this.socket.readyState === WS_OPEN || this.socket.readyState === WS_CONNECTING) {
        this.socket.close();
      }
      this.socket = null;
    }

    const baseWs = obtenerUrlWebSocket(this.urlServidor);
    const url = `${baseWs}/ws?id_sesion=${encodeURIComponent(idSesion)}&id_grupo=${encodeURIComponent(idGrupo)}&nombre=${encodeURIComponent(nombre)}`;
    this._ultimaUrlWs = url;

    this.socket = new WebSocket(url);

    this._manejadorMensaje = (evento) => {
      try {
        const datos = JSON.parse(evento.data);
        this._procesarMensajeEntrante(datos);
      } catch (error) {
        console.error('Mensaje WebSocket invalido:', error);
      }
    };

    this.socket.onopen = () => {
      this._conexionEnProgreso = false;
      this.intentosReconexion = 0;
      this._reconexionProgramada = false;
      if (this.callbacks.onConectado) {
        this.callbacks.onConectado();
      }
    };

    this.socket.onclose = (evento) => {
      this._conexionEnProgreso = false;
      this.detenerPingPong();

      if (this._reemplazandoSocket) {
        this._reemplazandoSocket = false;
        return;
      }

      if (evento.code >= 4001 && evento.code <= 4004) {
        this._desconexionIntencional = true;
        if (this.callbacks.onSesionInvalida) {
          this.callbacks.onSesionInvalida(evento.reason || 'Sesion rechazada por el servidor');
        }
        if (this.callbacks.onDesconectado) {
          this.callbacks.onDesconectado(evento.reason);
        }
        return;
      }

      if (this.callbacks.onDesconectado) {
        this.callbacks.onDesconectado(evento.reason || `codigo ${evento.code}`);
      }

      if (!this._desconexionIntencional && this._sesionActiva) {
        this._programarReconexion();
      }
    };

    this.socket.onerror = (evento) => {
      this._conexionEnProgreso = false;
      console.warn('WebSocket error:', this._ultimaUrlWs, evento?.message || '');
      if (this.callbacks.onErrorConexion) {
        this.callbacks.onErrorConexion(new Error('Error de transporte WebSocket'));
      }
    };

    this.socket.onmessage = this._manejadorMensaje;
    this.iniciarPingPong();
  }

  iniciarPingPong() {
    this.detenerPingPong();
    this.intervaloPingPong = setInterval(() => {
      if (this.estaConectado()) {
        try {
          this.socket.send(JSON.stringify({ type: 'ping' }));
        } catch (error) {
          console.error('Error al enviar ping:', error);
        }
      }
    }, 20000);
  }

  detenerPingPong() {
    if (this.intervaloPingPong) {
      clearInterval(this.intervaloPingPong);
      this.intervaloPingPong = null;
    }
  }

  async enviarSenal(idEvento, timestamp) {
    return new Promise((resolve, reject) => {
      if (!this.estaConectado()) {
        reject(new Error('WebSocket no conectado'));
        return;
      }

      const mensaje = { type: 'signal', event_id: idEvento, timestamp };
      const timeout = setTimeout(() => {
        if (this.socket) {
          this.socket.removeEventListener('message', handlerAck);
        }
        reject(new Error('Timeout esperando ACK'));
      }, 5000);

      const handlerAck = (evento) => {
        try {
          const datos = JSON.parse(evento.data);
          if (datos.type !== 'ack' || datos.event_id !== idEvento) {
            return;
          }
          clearTimeout(timeout);
          this.socket.removeEventListener('message', handlerAck);
          if (datos.status === 'success' || datos.status === 'duplicate') {
            resolve(datos);
          } else {
            reject(new Error('Error al enviar senal'));
          }
        } catch {
          // ignorar
        }
      };

      this.socket.addEventListener('message', handlerAck);
      this.socket.send(JSON.stringify(mensaje));
    });
  }

  desconectarWebSocket(intencional = true) {
    this._desconexionIntencional = intencional;
    this._limpiarTimeoutReconexion();
    this._reconexionProgramada = false;
    this._conexionEnProgreso = false;
    this.detenerPingPong();

    if (this.socket) {
      this.socket.onopen = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;
      if (this.socket.readyState === WS_OPEN || this.socket.readyState === WS_CONNECTING) {
        this.socket.close(1000, 'Cierre del cliente');
      }
      this.socket = null;
    }

    if (intencional) {
      this._sesionActiva = null;
      this.callbacks = {};
      this.intentosReconexion = 0;
      this._manejadorMensaje = null;
    }
  }

  estaConectado() {
    return this.socket && this.socket.readyState === WS_OPEN;
  }

  obtenerEstadoReal() {
    if (this.estaConectado()) {
      return 'conectado';
    }
    if (this.socket?.readyState === WS_CONNECTING || this._conexionEnProgreso) {
      return 'reconectando';
    }
    if (
      this._sesionActiva &&
      !this._desconexionIntencional &&
      (this._reconexionProgramada || this.intentosReconexion < this.maxIntentosReconexion)
    ) {
      return 'reconectando';
    }
    return 'desconectado';
  }

  esCierreIntencional() {
    return this._desconexionIntencional;
  }

  asegurarConexion(timeoutMs = 6000) {
    if (this.estaConectado()) {
      return Promise.resolve(true);
    }
    if (!this._sesionActiva || this._desconexionIntencional) {
      return Promise.resolve(false);
    }

    if (
      !this._conexionEnProgreso &&
      !this._reconexionProgramada &&
      (!this.socket || this.socket.readyState === WS_CLOSED)
    ) {
      const { idSesion, idGrupo, nombre, callbacks } = this._sesionActiva;
      this._abrirWebSocket(idSesion, idGrupo, nombre, callbacks);
    }

    return new Promise((resolve) => {
      const limite = Date.now() + timeoutMs;
      const intervalo = setInterval(() => {
        if (this.estaConectado()) {
          clearInterval(intervalo);
          resolve(true);
          return;
        }
        if (Date.now() >= limite || this._desconexionIntencional) {
          clearInterval(intervalo);
          resolve(false);
        }
      }, 300);
    });
  }

  async verificarSalud() {
    try {
      const respuesta = await fetch(`${this.urlServidor}/health`);
      if (!respuesta.ok) {
        throw new Error('Servidor no saludable');
      }
      return await respuesta.json();
    } catch (error) {
      console.error('Error al verificar salud del servidor:', error);
      throw error;
    }
  }
}

export const servicioConexion = new ServicioConexion();
