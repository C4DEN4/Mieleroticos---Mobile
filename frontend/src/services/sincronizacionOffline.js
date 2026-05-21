import { servicioConexion } from './conexionServidor';
import { servicioAlmacenamientoLocal } from './almacenamientoLocal';

const MENSAJE_SENAL_PROPIA = (nombre) => `${nombre} ha enviado una señal!`;

export async function sincronizarSenalesPendientes(usuario, agregarPeticion) {
  const pendientes = await servicioAlmacenamientoLocal.obtenerSenalesPendientes();
  if (!pendientes.length) {
    return 0;
  }

  let sincronizadas = 0;

  for (let indice = 0; indice < pendientes.length; indice++) {
    const senal = pendientes[indice];

    if (!servicioConexion.estaConectado()) {
      break;
    }

    try {
      const respuesta = await servicioConexion.enviarSenal(senal.idEvento, senal.timestamp);

      if (respuesta.status === 'success' || respuesta.status === 'duplicate') {
        const peticion = {
          remitente: senal.remitente || usuario,
          mensaje: MENSAJE_SENAL_PROPIA(senal.remitente || usuario),
          timestamp: senal.timestamp,
        };
        agregarPeticion(peticion);
        await servicioAlmacenamientoLocal.agregarPeticionHistorial(peticion, senal.idGrupo);
        await servicioAlmacenamientoLocal.eliminarSenalPendiente(0);
        sincronizadas += 1;
        indice -= 1;
      }
    } catch (error) {
      console.error('Error al sincronizar señal pendiente:', error);
      if (error.message.includes('conectado')) {
        break;
      }
    }
  }

  return sincronizadas;
}

export async function registrarSenalLocal(usuario, idGrupo, idEvento, timestamp, agregarPeticion) {
  const peticion = {
    remitente: usuario,
    mensaje: MENSAJE_SENAL_PROPIA(usuario),
    timestamp,
  };

  agregarPeticion(peticion);
  await servicioAlmacenamientoLocal.agregarPeticionHistorial(peticion, idGrupo);
}

export async function encolarSenalOffline(idGrupo, idEvento, timestamp, usuario) {
  await servicioAlmacenamientoLocal.guardarSenalPendiente({
    idEvento,
    timestamp,
    remitente: usuario,
    idGrupo,
  });
}
