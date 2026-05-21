import Constants from 'expo-constants';
import { Platform } from 'react-native';

const PUERTO_BFF = 8000;

/**
 * Si usas Expo Go en el celular, define la IP de tu PC en .env:
 * EXPO_PUBLIC_BFF_HOST=192.168.1.10
 *
 * Inicia Expo en modo LAN (no tunnel):
 * npx expo start --lan
 */
function obtenerHostDesarrollo() {
  const hostManual = process.env.EXPO_PUBLIC_BFF_HOST;
  if (hostManual && hostManual.trim()) {
    return hostManual.trim();
  }

  const hostUri =
    Constants.expoConfig?.hostUri ??
    Constants.manifest2?.extra?.expoGo?.debuggerHost ??
    Constants.manifest?.debuggerHost;

  if (hostUri) {
    const host = hostUri.split(':')[0];
    if (host && !host.includes('exp.') && !host.includes('tunnel')) {
      return host;
    }
  }

  if (Platform.OS === 'android') {
    return '10.0.2.2';
  }

  return 'localhost';
}

export function obtenerUrlServidor() {
  const host = obtenerHostDesarrollo();
  return `http://${host}:${PUERTO_BFF}`;
}

export function obtenerUrlWebSocket(urlHttp) {
  return urlHttp.replace(/^http/i, 'ws');
}
