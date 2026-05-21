import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useContextoAplicacion } from '../context/ContextoAplicacion';
import { obtenerTextoEstadoConexion, obtenerColorEstadoConexion } from '../utils/validaciones';

const IndicadorConexion = () => {
  const { estadoConexion, fuerzaSenal, URL_SERVIDOR } = useContextoAplicacion();

  const obtenerIconoEstado = () => {
    switch (estadoConexion) {
      case 'conectado':
        return 'wifi';
      case 'reconectando':
        return 'refresh';
      case 'desconectado':
        return 'wifi-outline';
      default:
        return 'help-outline';
    }
  };

  const obtenerIconoSenal = () => {
    if (fuerzaSenal >= 75) return 'cellular';
    if (fuerzaSenal >= 50) return 'cellular-outline';
    if (fuerzaSenal >= 25) return 'cellular-outline';
    return 'cellular-outline';
  };

  return (
    <View style={estilos.contenedor}>
      <View style={estilos.contenedorEstado}>
        <Ionicons
          name={obtenerIconoEstado()}
          size={20}
          color={obtenerColorEstadoConexion(estadoConexion)}
        />
        <Text style={[estilos.textoEstado, { color: obtenerColorEstadoConexion(estadoConexion) }]}>
          {obtenerTextoEstadoConexion(estadoConexion)}
        </Text>
      </View>
      
      {estadoConexion === 'conectado' && (
        <View style={estilos.contenedorSenal}>
          <Ionicons
            name={obtenerIconoSenal()}
            size={16}
            color="#8E8E93"
          />
          <Text style={estilos.textoSenal}>
            {fuerzaSenal}%
          </Text>
        </View>
      )}
      {estadoConexion !== 'conectado' && (
        <Text style={estilos.textoServidor} numberOfLines={1}>
          {URL_SERVIDOR}
        </Text>
      )}
    </View>
  );
};

const estilos = StyleSheet.create({
  contenedor: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  contenedorEstado: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  textoEstado: {
    fontSize: 14,
    fontWeight: '600',
  },
  contenedorSenal: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  textoSenal: {
    fontSize: 12,
    color: '#8E8E93',
  },
  textoServidor: {
    fontSize: 10,
    color: '#8E8E93',
    maxWidth: 140,
  },
});

export default IndicadorConexion;
