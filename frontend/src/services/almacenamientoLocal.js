import AsyncStorage from '@react-native-async-storage/async-storage';

class ServicioAlmacenamientoLocal {
  constructor() {
    this.CLAVE_USUARIO = '@usuario';
    this.CLAVE_SESION = '@sesion';
    this.CLAVE_GRUPO = '@grupo';
    this.CLAVE_HISTORIAL = '@historial';
    this.CLAVE_PENDIENTES = '@pendientes';
  }

  // Guardar datos del usuario
  async guardarUsuario(datosUsuario) {
    try {
      await AsyncStorage.setItem(this.CLAVE_USUARIO, JSON.stringify(datosUsuario));
      return true;
    } catch (error) {
      console.error('Error al guardar usuario:', error);
      return false;
    }
  }

  // Obtener datos del usuario
  async obtenerUsuario() {
    try {
      const datos = await AsyncStorage.getItem(this.CLAVE_USUARIO);
      return datos ? JSON.parse(datos) : null;
    } catch (error) {
      console.error('Error al obtener usuario:', error);
      return null;
    }
  }

  // Eliminar datos del usuario
  async eliminarUsuario() {
    try {
      await AsyncStorage.removeItem(this.CLAVE_USUARIO);
      return true;
    } catch (error) {
      console.error('Error al eliminar usuario:', error);
      return false;
    }
  }

  // Guardar sesión
  async guardarSesion(datosSesion) {
    try {
      await AsyncStorage.setItem(this.CLAVE_SESION, JSON.stringify(datosSesion));
      return true;
    } catch (error) {
      console.error('Error al guardar sesión:', error);
      return false;
    }
  }

  // Obtener sesión
  async obtenerSesion() {
    try {
      const datos = await AsyncStorage.getItem(this.CLAVE_SESION);
      return datos ? JSON.parse(datos) : null;
    } catch (error) {
      console.error('Error al obtener sesión:', error);
      return null;
    }
  }

  // Eliminar sesión
  async eliminarSesion() {
    try {
      await AsyncStorage.removeItem(this.CLAVE_SESION);
      return true;
    } catch (error) {
      console.error('Error al eliminar sesión:', error);
      return false;
    }
  }

  // Guardar datos del grupo
  async guardarGrupo(datosGrupo) {
    try {
      await AsyncStorage.setItem(this.CLAVE_GRUPO, JSON.stringify(datosGrupo));
      return true;
    } catch (error) {
      console.error('Error al guardar grupo:', error);
      return false;
    }
  }

  // Obtener datos del grupo
  async obtenerGrupo() {
    try {
      const datos = await AsyncStorage.getItem(this.CLAVE_GRUPO);
      return datos ? JSON.parse(datos) : null;
    } catch (error) {
      console.error('Error al obtener grupo:', error);
      return null;
    }
  }

  // Eliminar datos del grupo
  async eliminarGrupo() {
    try {
      await AsyncStorage.removeItem(this.CLAVE_GRUPO);
      return true;
    } catch (error) {
      console.error('Error al eliminar grupo:', error);
      return false;
    }
  }

  _claveHistorialGrupo(idGrupo) {
    return `${this.CLAVE_HISTORIAL}:${idGrupo || 'default'}`;
  }

  // Guardar historial de peticiones por grupo
  async guardarHistorial(historial, idGrupo) {
    try {
      await AsyncStorage.setItem(this._claveHistorialGrupo(idGrupo), JSON.stringify(historial));
      return true;
    } catch (error) {
      console.error('Error al guardar historial:', error);
      return false;
    }
  }

  // Obtener historial de peticiones del grupo
  async obtenerHistorial(idGrupo) {
    try {
      const datos = await AsyncStorage.getItem(this._claveHistorialGrupo(idGrupo));
      return datos ? JSON.parse(datos) : [];
    } catch (error) {
      console.error('Error al obtener historial:', error);
      return [];
    }
  }

  // Agregar petición al historial del grupo
  async agregarPeticionHistorial(peticion, idGrupo) {
    try {
      const historial = await this.obtenerHistorial(idGrupo);
      const duplicada = historial.some(
        (p) =>
          p.remitente === peticion.remitente &&
          p.timestamp === peticion.timestamp &&
          p.mensaje === peticion.mensaje
      );
      if (duplicada) {
        return true;
      }
      const nuevoHistorial = [peticion, ...historial].slice(0, 100);
      await this.guardarHistorial(nuevoHistorial, idGrupo);
      return true;
    } catch (error) {
      console.error('Error al agregar petición al historial:', error);
      return false;
    }
  }

  // Limpiar historial de un grupo
  async limpiarHistorial(idGrupo) {
    try {
      await AsyncStorage.removeItem(this._claveHistorialGrupo(idGrupo));
      return true;
    } catch (error) {
      console.error('Error al limpiar historial:', error);
      return false;
    }
  }

  // Guardar señales pendientes (para sincronización offline)
  async guardarSenalPendiente(senal) {
    try {
      const pendientes = await this.obtenerSenalesPendientes();
      const duplicada = pendientes.some((p) => p.idEvento === senal.idEvento);
      if (duplicada) {
        return true;
      }
      pendientes.push(senal);
      await AsyncStorage.setItem(this.CLAVE_PENDIENTES, JSON.stringify(pendientes));
      return true;
    } catch (error) {
      console.error('Error al guardar señal pendiente:', error);
      return false;
    }
  }

  // Obtener señales pendientes
  async obtenerSenalesPendientes() {
    try {
      const datos = await AsyncStorage.getItem(this.CLAVE_PENDIENTES);
      return datos ? JSON.parse(datos) : [];
    } catch (error) {
      console.error('Error al obtener señales pendientes:', error);
      return [];
    }
  }

  // Eliminar señal pendiente
  async eliminarSenalPendiente(indice) {
    try {
      const pendientes = await this.obtenerSenalesPendientes();
      pendientes.splice(indice, 1);
      await AsyncStorage.setItem(this.CLAVE_PENDIENTES, JSON.stringify(pendientes));
      return true;
    } catch (error) {
      console.error('Error al eliminar señal pendiente:', error);
      return false;
    }
  }

  // Limpiar todas las señales pendientes
  async limpiarSenalesPendientes() {
    try {
      await AsyncStorage.removeItem(this.CLAVE_PENDIENTES);
      return true;
    } catch (error) {
      console.error('Error al limpiar señales pendientes:', error);
      return false;
    }
  }

  // Limpiar todos los datos (logout completo)
  async limpiarTodo() {
    try {
      await AsyncStorage.multiRemove([
        this.CLAVE_USUARIO,
        this.CLAVE_SESION,
        this.CLAVE_GRUPO,
        this.CLAVE_HISTORIAL,
        this.CLAVE_PENDIENTES,
      ]);
      return true;
    } catch (error) {
      console.error('Error al limpiar todos los datos:', error);
      return false;
    }
  }
}

// Exportar instancia única
export const servicioAlmacenamientoLocal = new ServicioAlmacenamientoLocal();
