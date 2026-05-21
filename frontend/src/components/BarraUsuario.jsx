import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useContextoAplicacion } from '../context/ContextoAplicacion';

const BarraUsuario = ({ onCerrarSesion }) => {
  const { usuario } = useContextoAplicacion();

  return (
    <View style={estilos.contenedor}>
      <View style={estilos.contenedorUsuario}>
        <Text style={estilos.nombreUsuario}>{usuario}</Text>
      </View>
      
      <TouchableOpacity
        style={estilos.botonCerrarSesion}
        onPress={onCerrarSesion}
      >
        <Ionicons name="log-out-outline" size={24} color="#FF3B30" />
      </TouchableOpacity>
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
  contenedorUsuario: {
    flex: 1,
    alignItems: 'center',
  },
  nombreUsuario: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000000',
  },
  botonCerrarSesion: {
    padding: 8,
    backgroundColor: '#FF3B30' + '10',
    borderRadius: 8,
  },
});

export default BarraUsuario;
