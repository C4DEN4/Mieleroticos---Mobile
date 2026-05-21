// Utilidades de validación para el frontend

// Validar nombre de usuario
export const validarNombre = (nombre) => {
  if (!nombre || nombre.trim() === '') {
    return {
      valido: false,
      mensaje: 'El nombre es obligatorio',
    };
  }

  if (nombre.length > 30) {
    return {
      valido: false,
      mensaje: 'El nombre no puede exceder 30 caracteres',
    };
  }

  if (nombre.length < 2) {
    return {
      valido: false,
      mensaje: 'El nombre debe tener al menos 2 caracteres',
    };
  }

  // Validar que no contenga caracteres especiales peligrosos
  const regex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-_]+$/;
  if (!regex.test(nombre)) {
    return {
      valido: false,
      mensaje: 'El nombre solo puede contener letras, espacios, guiones y guiones bajos',
    };
  }

  return {
    valido: true,
    mensaje: '',
  };
};

// Validar ID de grupo
export const validarGrupo = (idGrupo) => {
  if (!idGrupo || idGrupo.trim() === '') {
    return {
      valido: false,
      mensaje: 'El grupo es obligatorio',
    };
  }

  if (idGrupo.length > 50) {
    return {
      valido: false,
      mensaje: 'El ID del grupo no puede exceder 50 caracteres',
    };
  }

  return {
    valido: true,
    mensaje: '',
  };
};

// Validar formulario de autenticación
export const validarFormularioAutenticacion = (nombre, idGrupo) => {
  const validacionNombre = validarNombre(nombre);
  const validacionGrupo = validarGrupo(idGrupo);

  if (!validacionNombre.valido) {
    return validacionNombre;
  }

  if (!validacionGrupo.valido) {
    return validacionGrupo;
  }

  return {
    valido: true,
    mensaje: '',
  };
};

// Generar ID de evento único (UUID v4 — requerido por el servicio de Grupos)
export const generarIdEvento = () => {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return globalThis.crypto.randomUUID();
  }
  const segmento = () =>
    Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
  return `${segmento()}${segmento()}-${segmento()}-4${segmento().slice(0, 3)}-a${segmento().slice(0, 3)}-${segmento()}${segmento()}${segmento()}`;
};

// Formatear timestamp a hora legible
export const formatearTimestamp = (timestamp) => {
  if (!timestamp) return '--:--:--';
  
  const fecha = new Date(timestamp);
  const horas = fecha.getHours().toString().padStart(2, '0');
  const minutos = fecha.getMinutes().toString().padStart(2, '0');
  const segundos = fecha.getSeconds().toString().padStart(2, '0');
  
  return `${horas}:${minutos}:${segundos}`;
};

// Formatear fecha completa
export const formatearFechaCompleta = (timestamp) => {
  if (!timestamp) return '';
  
  const fecha = new Date(timestamp);
  const dia = fecha.getDate().toString().padStart(2, '0');
  const mes = (fecha.getMonth() + 1).toString().padStart(2, '0');
  const anio = fecha.getFullYear();
  const horas = fecha.getHours().toString().padStart(2, '0');
  const minutos = fecha.getMinutes().toString().padStart(2, '0');
  
  return `${dia}/${mes}/${anio} ${horas}:${minutos}`;
};

// Validar URL del servidor
export const validarURLServidor = (url) => {
  if (!url || url.trim() === '') {
    return {
      valido: false,
      mensaje: 'La URL del servidor es obligatoria',
    };
  }

  try {
    new URL(url);
    return {
      valido: true,
      mensaje: '',
    };
  } catch (error) {
    return {
      valido: false,
      mensaje: 'La URL del servidor no es válida',
    };
  }
};

// Obtener color temático para grupo
export const obtenerColorGrupo = (idGrupo) => {
  const colores = {
    'grupo-a': '#007AFF', // Azul
    'grupo-b': '#FF9500', // Naranja
    'grupo-c': '#34C759', // Verde
    'grupo-d': '#AF52DE', // Púrpura
    'grupo-e': '#FF3B30', // Rojo
  };

  // Buscar coincidencia exacta (case-insensitive)
  const clave = Object.keys(colores).find(
    (k) => k.toLowerCase() === idGrupo.toLowerCase()
  );

  if (clave) {
    return colores[clave];
  }

  // Si no hay coincidencia, generar color basado en hash del ID
  let hash = 0;
  for (let i = 0; i < idGrupo.length; i++) {
    hash = idGrupo.charCodeAt(i) + ((hash << 5) - hash);
  }

  const coloresPorDefecto = ['#007AFF', '#FF9500', '#34C759', '#AF52DE', '#FF3B30', '#5856D6'];
  return coloresPorDefecto[Math.abs(hash) % coloresPorDefecto.length];
};

// Validar estado de conexión
export const obtenerTextoEstadoConexion = (estado) => {
  const textos = {
    conectado: 'Conectado al servidor',
    reconectando: 'Sincronizando datos...',
    desconectado: 'Sin conexión - Modo local activo',
  };

  return textos[estado] || 'Estado desconocido';
};

// Obtener color para estado de conexión
export const obtenerColorEstadoConexion = (estado) => {
  const colores = {
    conectado: '#34C759', // Verde
    reconectando: '#FF9500', // Naranja
    desconectado: '#FF3B30', // Rojo
  };

  return colores[estado] || '#8E8E93'; // Gris por defecto
};

// Truncar texto si es muy largo
export const truncarTexto = (texto, longitudMaxima = 50) => {
  if (!texto) return '';
  
  if (texto.length <= longitudMaxima) {
    return texto;
  }

  return texto.substring(0, longitudMaxima - 3) + '...';
};

// Validar que un objeto no esté vacío
export const validarObjetoNoVacio = (objeto) => {
  if (!objeto) return false;
  
  return Object.keys(objeto).length > 0;
};

// Sanitizar entrada de texto
export const sanitizarTexto = (texto) => {
  if (!texto) return '';
  
  return texto
    .trim()
    .replace(/[<>]/g, '') // Eliminar caracteres HTML peligrosos
    .substring(0, 100); // Limitar longitud
};
