import React from 'react';
import { ProveedorContextoAplicacion } from './src/context/ContextoAplicacion';
import Navegacion from './src/navegacion/Navegacion';

export default function App() {
  return (
    <ProveedorContextoAplicacion>
      <Navegacion />
    </ProveedorContextoAplicacion>
  );
}
