import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useContextoAplicacion } from '../context/ContextoAplicacion';
import { obtenerColorGrupo } from '../utils/validaciones';

const TarjetaGrupo = () => {
  const { nombreGrupo, idGrupo, miembrosGrupo, totalMiembros, usuario } = useContextoAplicacion();
  const colorGrupo = obtenerColorGrupo(idGrupo || nombreGrupo.toLowerCase().replace(/\s+/g, '-'));

  return (
    <View style={[estilos.contenedor, { borderTopColor: colorGrupo }]}>
      {/* Encabezado del grupo */}
      <View style={estilos.encabezado}>
        <View style={estilos.contenedorNombre}>
          <View style={[estilos.indicadorColor, { backgroundColor: colorGrupo }]} />
          <Text style={estilos.nombreGrupo}>{nombreGrupo}</Text>
        </View>
        <Text style={estilos.totalMiembros}>
          {totalMiembros} estudiante{totalMiembros !== 1 ? 's' : ''} en línea
        </Text>
      </View>

      {/* Lista de miembros */}
      <View style={estilos.contenedorMiembros}>
        <Text style={estilos.tituloMiembros}>Miembros activos:</Text>
        
        {miembrosGrupo.length > 0 ? (
          <ScrollView 
            style={estilos.listaMiembros}
            showsVerticalScrollIndicator={false}
          >
            {miembrosGrupo.map((miembro, indice) => (
              <View
                key={indice}
                style={[
                  estilos.itemMiembro,
                  miembro === usuario && estilos.itemMiembroPropio
                ]}
              >
                <Ionicons
                  name="person-circle-outline"
                  size={20}
                  color={miembro === usuario ? colorGrupo : '#8E8E93'}
                />
                <Text style={[
                  estilos.nombreMiembro,
                  miembro === usuario && { color: colorGrupo, fontWeight: 'bold' }
                ]}>
                  {miembro}
                  {miembro === usuario && ' (Tú)'}
                </Text>
              </View>
            ))}
          </ScrollView>
        ) : (
          <View style={estilos.contenedorVacio}>
            <Ionicons name="people-outline" size={32} color="#C7C7CC" />
            <Text style={estilos.textoVacio}>No hay miembros conectados</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const estilos = StyleSheet.create({
  contenedor: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    margin: 16,
    borderTopWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
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
  contenedorNombre: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  indicadorColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  nombreGrupo: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000000',
  },
  totalMiembros: {
    fontSize: 14,
    color: '#8E8E93',
  },
  contenedorMiembros: {
    maxHeight: 200,
  },
  tituloMiembros: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
    marginBottom: 8,
  },
  listaMiembros: {
    maxHeight: 160,
  },
  itemMiembro: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    marginBottom: 6,
    gap: 8,
  },
  itemMiembroPropio: {
    backgroundColor: '#007AFF' + '10',
    borderWidth: 1,
    borderColor: '#007AFF' + '30',
  },
  nombreMiembro: {
    fontSize: 16,
    color: '#000000',
  },
  contenedorVacio: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  textoVacio: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 8,
  },
});

export default TarjetaGrupo;
