import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { useContextoAplicacion } from '../context/ContextoAplicacion';
import { servicioConexion } from '../services/conexionServidor';
import { servicioAlmacenamientoLocal } from '../services/almacenamientoLocal';
import { validarFormularioAutenticacion, obtenerColorGrupo } from '../utils/validaciones';

const PantallaAutenticacion = ({ navigation }) => {
  const { establecerUsuario, URL_SERVIDOR } = useContextoAplicacion();

  const [nombre, setNombre] = useState('');
  const [grupoSeleccionado, setGrupoSeleccionado] = useState('');
  const [gruposDisponibles, setGruposDisponibles] = useState([
    { id: 'grupo-a', nombre: 'Grupo A' },
    { id: 'grupo-b', nombre: 'Grupo B' },
    { id: 'grupo-c', nombre: 'Grupo C' },
    { id: 'grupo-d', nombre: 'Grupo D' }
  ]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState('');
  const [selectorVisible, setSelectorVisible] = useState(false);

  // Establecer URL del servidor
  useEffect(() => {
    servicioConexion.establecerURL(URL_SERVIDOR);
  }, [URL_SERVIDOR]);

  // Validar formulario
  const formularioValido = () => {
    const validacion = validarFormularioAutenticacion(nombre, grupoSeleccionado);
    return validacion.valido;
  };

  // Manejar ingreso al sistema
  const manejarIngreso = async () => {
    // Validar formulario
    const validacion = validarFormularioAutenticacion(nombre, grupoSeleccionado);
    if (!validacion.valido) {
      setError(validacion.mensaje);
      return;
    }

    setError('');
    setCargando(true);

    try {
      // Crear sesión en el backend
      const respuestaSesion = await servicioConexion.crearSesion(
        nombre.trim(),
        grupoSeleccionado
      );

      // Guardar datos localmente
      await servicioAlmacenamientoLocal.guardarUsuario({
        nombre: nombre.trim(),
        idSesion: respuestaSesion.session_id,
        idGrupo: grupoSeleccionado,
        nombreGrupo: gruposDisponibles.find(g => g.id === grupoSeleccionado)?.nombre || grupoSeleccionado,
      });

      await servicioAlmacenamientoLocal.guardarSesion(respuestaSesion);

      // Establecer usuario en el contexto
      establecerUsuario({
        nombre: nombre.trim(),
        idSesion: respuestaSesion.session_id,
        idGrupo: grupoSeleccionado,
        nombreGrupo: gruposDisponibles.find(g => g.id === grupoSeleccionado)?.nombre || grupoSeleccionado,
      });

      // Navegar a la pantalla principal
      navigation.replace('Hub');
    } catch (error) {
      console.error('Error al ingresar:', error);

      if (error.message.includes('ya existe') || error.message.includes('duplicado') || error.message.includes('en uso')) {
        setError('Este nombre ya está en uso en este grupo. Por favor, elige otro nombre.');
      } else if (error.message.includes('Servicio no disponible')) {
        setError('El servidor no está disponible. Intenta nuevamente más tarde.');
      } else {
        setError('Error al conectar. Por favor, verifica tu conexión e intenta nuevamente.');
      }
    } finally {
      setCargando(false);
    }
  };

  // Renderizar selector de grupos
  const renderizarSelectorGrupos = () => {
    return (
      <View style={estilos.contenedorSelector}>
        <Text style={estilos.etiqueta}>Selecciona tu grupo:</Text>

        <TouchableOpacity
          style={[
            estilos.botonSelector,
            { borderColor: grupoSeleccionado ? obtenerColorGrupo(grupoSeleccionado) : '#C7C7CC' }
          ]}
          onPress={() => setSelectorVisible(!selectorVisible)}
        >
          <Text style={[
            estilos.textoBotonSelector,
            { color: grupoSeleccionado ? obtenerColorGrupo(grupoSeleccionado) : '#8E8E93' }
          ]}>
            {grupoSeleccionado
              ? gruposDisponibles.find(g => g.id === grupoSeleccionado)?.nombre || grupoSeleccionado
              : 'Seleccionar grupo...'}
          </Text>
        </TouchableOpacity>

        {selectorVisible && (
          <View style={estilos.listaGrupos}>
            {gruposDisponibles.map((grupo) => (
              <TouchableOpacity
                key={grupo.id}
                style={[
                  estilos.itemGrupo,
                  grupoSeleccionado === grupo.id && { backgroundColor: obtenerColorGrupo(grupo.id) + '20' }
                ]}
                onPress={() => {
                  setGrupoSeleccionado(grupo.id);
                  setSelectorVisible(false);
                  setError('');
                }}
              >
                <View style={[
                  estilos.indicadorGrupo,
                  { backgroundColor: obtenerColorGrupo(grupo.id) }
                ]} />
                <Text style={[
                  estilos.textoItemGrupo,
                  grupoSeleccionado === grupo.id && { fontWeight: 'bold' }
                ]}>
                  {grupo.nombre}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={estilos.contenedorSeguro}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={estilos.contenedor}
      >
        <ScrollView contentContainerStyle={estilos.contenidoScroll}>
          <View style={estilos.contenedorPrincipal}>
            {/* Título */}
            <View style={estilos.contenedorTitulo}>
              <Text style={estilos.titulo}>Classroom Hub</Text>
              <Text style={estilos.subtitulo}>Sistema Distribuido de Aula</Text>
            </View>

            {/* Formulario */}
            <View style={estilos.contenedorFormulario}>
              {/* Campo de nombre */}
              <View style={estilos.contenedorCampo}>
                <Text style={estilos.etiqueta}>Tu nombre:</Text>
                <TextInput
                  style={[
                    estilos.campoTexto,
                    error && error.includes('nombre') && estilos.campoError
                  ]}
                  placeholder="Ingresa tu nombre"
                  value={nombre}
                  onChangeText={(texto) => {
                    setNombre(texto);
                    setError('');
                  }}
                  maxLength={30}
                  autoCapitalize="words"
                  autoComplete="name"
                />
                <Text style={estilos.contadorCaracteres}>
                  {nombre.length}/30 caracteres
                </Text>
              </View>

              {/* Selector de grupo */}
              {renderizarSelectorGrupos()}

              {/* Mensaje de error */}
              {error ? (
                <View style={estilos.contenedorError}>
                  <Text style={estilos.textoError}>{error}</Text>
                </View>
              ) : null}

              {/* Botón de ingreso */}
              <TouchableOpacity
                style={[
                  estilos.botonIngreso,
                  !formularioValido() && estilos.botonDeshabilitado,
                  cargando && estilos.botonCargando,
                ]}
                onPress={manejarIngreso}
                disabled={!formularioValido() || cargando}
              >
                {cargando ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={estilos.textoBotonIngreso}>
                    {formularioValido() ? 'Ingresar' : 'Completa los campos'}
                  </Text>
                )}
              </TouchableOpacity>

              {/* Información adicional */}
              <View style={estilos.contenedorInfo}>
                <Text style={estilos.textoInfo}>
                  Asegurate de tener conexion a internet para ingresar.
                </Text>
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const estilos = StyleSheet.create({
  contenedorSeguro: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  contenedor: {
    flex: 1,
  },
  contenidoScroll: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  contenedorPrincipal: {
    flex: 1,
    justifyContent: 'center',
  },
  contenedorTitulo: {
    alignItems: 'center',
    marginBottom: 40,
  },
  titulo: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 8,
  },
  subtitulo: {
    fontSize: 16,
    color: '#8E8E93',
  },
  contenedorFormulario: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  contenedorCampo: {
    marginBottom: 20,
  },
  etiqueta: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 8,
  },
  campoTexto: {
    borderWidth: 1,
    borderColor: '#C7C7CC',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#F2F2F7',
  },
  campoError: {
    borderColor: '#FF3B30',
  },
  contadorCaracteres: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 4,
    textAlign: 'right',
  },
  contenedorSelector: {
    marginBottom: 20,
  },
  botonSelector: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    backgroundColor: '#F2F2F7',
  },
  textoBotonSelector: {
    fontSize: 16,
  },
  listaGrupos: {
    marginTop: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#C7C7CC',
    maxHeight: 200,
  },
  itemGrupo: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  indicadorGrupo: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  textoItemGrupo: {
    fontSize: 16,
    color: '#000000',
  },
  contenedorError: {
    backgroundColor: '#FF3B30' + '10',
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
  },
  textoError: {
    color: '#FF3B30',
    fontSize: 14,
  },
  botonIngreso: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 16,
  },
  botonDeshabilitado: {
    backgroundColor: '#C7C7CC',
  },
  botonCargando: {
    opacity: 0.7,
  },
  textoBotonIngreso: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  contenedorInfo: {
    alignItems: 'center',
  },
  textoInfo: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
});

export default PantallaAutenticacion;
