import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { obtenerUrlServidor } from '../config/api';

const ContextoAplicacion = createContext();

export const useContextoAplicacion = () => {
  const contexto = useContext(ContextoAplicacion);
  if (!contexto) {
    throw new Error('useContextoAplicacion debe ser usado dentro de un ProveedorContextoAplicacion');
  }
  return contexto;
};

export const ProveedorContextoAplicacion = ({ children }) => {
  const [usuario, setUsuario] = useState(null);
  const [idSesion, setIdSesion] = useState(null);
  const [idGrupo, setIdGrupo] = useState(null);
  const [estadoConexion, setEstadoConexion] = useState('desconectado');
  const [fuerzaSenal, setFuerzaSenal] = useState(0);
  const [nombreGrupo, setNombreGrupo] = useState('');
  const [miembrosGrupo, setMiembrosGrupo] = useState([]);
  const [totalMiembros, setTotalMiembros] = useState(0);
  const [historialPeticiones, setHistorialPeticiones] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  const URL_SERVIDOR = useMemo(() => obtenerUrlServidor(), []);
  const [wsListo, setWsListo] = useState(false);

  const establecerUsuario = useCallback((datosUsuario) => {
    setUsuario(datosUsuario.nombre);
    setIdSesion(datosUsuario.idSesion);
    setIdGrupo(datosUsuario.idGrupo);
    setNombreGrupo(datosUsuario.nombreGrupo);
  }, []);

  const limpiarSesion = useCallback(() => {
    setUsuario(null);
    setIdSesion(null);
    setIdGrupo(null);
    setNombreGrupo('');
    setMiembrosGrupo([]);
    setTotalMiembros(0);
    setHistorialPeticiones([]);
    setEstadoConexion('desconectado');
    setFuerzaSenal(0);
    setError(null);
  }, []);

  const actualizarEstadoConexion = useCallback((estado, fuerza = 0) => {
    setEstadoConexion(estado);
    setFuerzaSenal(fuerza);
  }, []);

  const actualizarMiembrosGrupo = useCallback((miembros) => {
    setMiembrosGrupo(miembros);
    setTotalMiembros(miembros.length);
  }, []);

  const agregarPeticion = useCallback((peticion) => {
    setHistorialPeticiones((prev) => {
      const existe = prev.some(
        (p) =>
          p.remitente === peticion.remitente &&
          p.timestamp === peticion.timestamp &&
          p.mensaje === peticion.mensaje
      );
      if (existe) {
        return prev;
      }
      return [peticion, ...prev].slice(0, 100);
    });
  }, []);

  const establecerHistorial = useCallback((historial) => {
    setHistorialPeticiones(historial.slice(0, 100));
  }, []);

  const establecerError = useCallback((mensajeError) => {
    setError(mensajeError);
  }, []);

  const limpiarError = useCallback(() => {
    setError(null);
  }, []);

  const valor = {
    usuario,
    idSesion,
    idGrupo,
    nombreGrupo,
    estadoConexion,
    wsListo,
    fuerzaSenal,
    miembrosGrupo,
    totalMiembros,
    historialPeticiones,
    cargando,
    error,
    URL_SERVIDOR,
    establecerUsuario,
    limpiarSesion,
    actualizarEstadoConexion,
    setWsListo,
    actualizarMiembrosGrupo,
    agregarPeticion,
    establecerHistorial,
    setCargando,
    establecerError,
    limpiarError,
  };

  return (
    <ContextoAplicacion.Provider value={valor}>
      {children}
    </ContextoAplicacion.Provider>
  );
};
