import React from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useContextoAplicacion } from '../context/ContextoAplicacion';
import { formatearTimestamp } from '../utils/validaciones';

const HistorialPeticiones = ({ onRefrescar }) => {
  const { historialPeticiones, usuario } = useContextoAplicacion();
  const [refrescando, setRefrescando] = React.useState(false);

  const manejarRefrescar = async () => {
    setRefrescando(true);
    if (onRefrescar) {
      await onRefrescar();
    }
    setRefrescando(false);
  };

  return (
    <View style={estilos.contenedor}>
      <View style={estilos.encabezado}>
        <Text style={estilos.titulo}>Historial del Grupo</Text>
        <Text style={estilos.contador}>
          {historialPeticiones.length} evento{historialPeticiones.length !== 1 ? 's' : ''}
        </Text>
      </View>

      <ScrollView
        style={estilos.lista}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refrescando}
            onRefresh={manejarRefrescar}
            colors={['#007AFF']}
          />
        }
      >
        {historialPeticiones.length > 0 ? (
          historialPeticiones.map((peticion, indice) => {
            const esPropia = peticion.remitente === usuario;
            
            return (
              <View
                key={`${peticion.timestamp}-${peticion.remitente}-${indice}`}
                style={[
                  estilos.item,
                  esPropia && estilos.itemPropio
                ]}
              >
                <View style={estilos.contenedorHora}>
                  <Text style={estilos.hora}>
                    {formatearTimestamp(peticion.timestamp)}
                  </Text>
                </View>
                
                <View style={estilos.contenedorContenido}>
                  <View style={estilos.contenedorRemitente}>
                    <Ionicons
                      name={esPropia ? 'checkmark-circle' : 'person-circle-outline'}
                      size={16}
                      color={esPropia ? '#34C759' : '#007AFF'}
                    />
                    <Text style={[
                      estilos.remitente,
                      esPropia && estilos.remitentePropio
                    ]}>
                      {peticion.remitente}
                    </Text>
                  </View>
                  
                  <Text style={estilos.mensaje}>
                    {peticion.mensaje}
                  </Text>
                </View>
              </View>
            );
          })
        ) : (
          <View style={estilos.contenedorVacio}>
            <Ionicons name="document-text-outline" size={48} color="#C7C7CC" />
            <Text style={estilos.textoVacio}>No hay señales enviadas aún</Text>
            <Text style={estilos.textoSecundario}>
              Sé el primero en enviar una señal
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const estilos = StyleSheet.create({
  contenedor: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    maxHeight: 300,
  },
  encabezado: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  titulo: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000000',
  },
  contador: {
    fontSize: 14,
    color: '#8E8E93',
  },
  lista: {
    maxHeight: 220,
  },
  item: {
    flexDirection: 'row',
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    marginBottom: 8,
    gap: 12,
  },
  itemPropio: {
    backgroundColor: '#34C759' + '10',
    borderWidth: 1,
    borderColor: '#34C759' + '30',
  },
  contenedorHora: {
    minWidth: 60,
  },
  hora: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '600',
  },
  contenedorContenido: {
    flex: 1,
  },
  contenedorRemitente: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  remitente: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  remitentePropio: {
    color: '#34C759',
  },
  mensaje: {
    fontSize: 14,
    color: '#000000',
  },
  contenedorVacio: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  textoVacio: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 12,
    fontWeight: '600',
  },
  textoSecundario: {
    fontSize: 14,
    color: '#C7C7CC',
    marginTop: 4,
  },
});

export default HistorialPeticiones;
