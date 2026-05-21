import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useContextoAplicacion } from '../context/ContextoAplicacion';
import { generarIdEvento } from '../utils/validaciones';

const BotonAccion = ({ onEnviarSenal }) => {
  const { wsListo, estadoConexion } = useContextoAplicacion();
  const [enviando, setEnviando] = useState(false);
  const [deshabilitado, setDeshabilitado] = useState(false);

  const manejarPresion = async () => {
    if (enviando || deshabilitado) {
      return;
    }

    setEnviando(true);
    setDeshabilitado(true);

    try {
      const idEvento = generarIdEvento();
      const timestamp = new Date().toISOString();

      if (onEnviarSenal) {
        await onEnviarSenal(idEvento, timestamp);
      }

      setTimeout(() => {
        setDeshabilitado(false);
      }, 1000);
    } catch (error) {
      console.error('Error al enviar señal:', error);
    } finally {
      setEnviando(false);
    }
  };

  const enLinea = wsListo && estadoConexion === 'conectado';
  const habilitado = !deshabilitado && !enviando;

  return (
    <View style={estilos.contenedor}>
      <TouchableOpacity
        style={[
          estilos.boton,
          habilitado && (enLinea ? estilos.botonHabilitado : estilos.botonOffline),
          !habilitado && estilos.botonDeshabilitado,
        ]}
        onPress={manejarPresion}
        disabled={!habilitado}
        activeOpacity={habilitado ? 0.7 : 1}
      >
        {enviando ? (
          <ActivityIndicator color="#FFFFFF" size="small" />
        ) : (
          <>
            <Ionicons
              name="send"
              size={24}
              color={habilitado ? '#FFFFFF' : '#8E8E93'}
            />
            <Text style={[estilos.textoBoton, !habilitado && estilos.textoBotonDeshabilitado]}>
              {enLinea ? 'Enviar Senal' : 'Encolar Senal (Offline)'}
            </Text>
          </>
        )}
      </TouchableOpacity>

      {!enLinea && habilitado && (
        <Text style={estilos.textoAyuda}>
          {estadoConexion === 'reconectando'
            ? 'Reconectando canal en tiempo real...'
            : 'Modo offline: las senales se encolan y sincronizan al reconectar'}
        </Text>
      )}
    </View>
  );
};

const estilos = StyleSheet.create({
  contenedor: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  boton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 12,
  },
  botonHabilitado: {
    backgroundColor: '#34C759',
    shadowColor: '#34C759',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  botonOffline: {
    backgroundColor: '#FF9500',
  },
  botonDeshabilitado: {
    backgroundColor: '#C7C7CC',
  },
  textoBoton: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  textoBotonDeshabilitado: {
    color: '#8E8E93',
  },
  textoAyuda: {
    fontSize: 14,
    color: '#FF9500',
    textAlign: 'center',
    marginTop: 8,
  },
});

export default BotonAccion;
