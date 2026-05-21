import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import PantallaAutenticacion from '../screens/PantallaAutenticacion';
import PantallaHub from '../screens/PantallaHub';
import { useContextoAplicacion } from '../context/ContextoAplicacion';
import { servicioAlmacenamientoLocal } from '../services/almacenamientoLocal';
import { servicioConexion } from '../services/conexionServidor';

const Stack = createNativeStackNavigator();

const Navegacion = () => {
  const { establecerUsuario, URL_SERVIDOR } = useContextoAplicacion();
  const [listo, setListo] = useState(false);
  const [rutaInicial, setRutaInicial] = useState('Autenticacion');

  useEffect(() => {
    const restaurarSesion = async () => {
      try {
        servicioConexion.establecerURL(URL_SERVIDOR);
        const datosUsuario = await servicioAlmacenamientoLocal.obtenerUsuario();

        if (datosUsuario?.idSesion && datosUsuario?.nombre && datosUsuario?.idGrupo) {
          try {
            await servicioConexion.verificarSalud();
            establecerUsuario(datosUsuario);
            setRutaInicial('Hub');
          } catch {
            establecerUsuario(datosUsuario);
            setRutaInicial('Hub');
          }
        }
      } catch (error) {
        console.error('Error al restaurar sesión:', error);
      } finally {
        setListo(true);
      }
    };

    restaurarSesion();
  }, [URL_SERVIDOR, establecerUsuario]);

  if (!listo) {
    return (
      <View style={estilos.cargando}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName={rutaInicial}
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen
          name="Autenticacion"
          component={PantallaAutenticacion}
          options={{ title: 'Autenticación' }}
        />
        <Stack.Screen
          name="Hub"
          component={PantallaHub}
          options={{ title: 'Hub Principal' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const estilos = StyleSheet.create({
  cargando: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
  },
});

export default Navegacion;
