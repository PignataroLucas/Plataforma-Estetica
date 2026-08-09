/**
 * La validación de la foto en el formulario de producto.
 *
 * El backend valida lo mismo (`ProductoCreateUpdateSerializer.validate_foto`,
 * con su test en `backend/apps/inventario/tests/test_foto_producto.py`), así
 * que esto no es la barrera de seguridad: es la que evita que alguien del
 * centro suba 12 MB por una conexión de local y recién ahí reciba un error de
 * campo. En la carga de fotos del catálogo, de a decenas y desde el celular,
 * las fotos que pasan el tope son lo normal, no la excepción.
 *
 * El `accept="image/*"` del input no alcanza y por eso el chequeo existe en JS:
 * es una sugerencia para el diálogo del sistema, y se la saltea cualquiera que
 * elija "todos los archivos" o arrastre algo a la ventana. Los tests usan
 * `applyAccept: false` justamente para reproducir ese camino, que es el único
 * en el que el `if` corre.
 */
import { render, screen, waitForElementToBeRemoved } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ProductoForm } from '../ProductoForm'

// El formulario pide categorías y proveedores al montarse. No es lo que se está
// probando; sin esto se queda en "Cargando...".
vi.mock('@/services/api', () => ({
  default: { get: vi.fn(async () => ({ data: [] })) },
}))

/**
 * El input de archivo no tiene label asociado (es un `<span>`), así que no hay
 * query accesible que lo encuentre. Se busca por tipo, con un error explícito
 * si el formulario cambia de forma.
 */
const inputDeFoto = (): HTMLInputElement => {
  const input = document.querySelector<HTMLInputElement>('input[type="file"]')
  if (!input) {
    throw new Error('No se encontró el input de foto en el formulario')
  }
  return input
}

const renderizarFormulario = async () => {
  // Sin `applyAccept: false`, user-event respeta el accept="image/*" del input
  // y descarta el archivo antes de que el handler lo vea: el test pasaría sin
  // haber ejecutado una sola línea de la validación.
  const usuario = userEvent.setup({ applyAccept: false })

  render(<ProductoForm onSubmit={vi.fn()} onCancel={vi.fn()} />)
  await waitForElementToBeRemoved(() => screen.queryByText('Cargando datos del formulario...'))

  return usuario
}

const archivoDe = (nombre: string, tipo: string, megas: number) =>
  new File([new Uint8Array(Math.round(megas * 1024 * 1024))], nombre, { type: tipo })

describe('la foto en ProductoForm', () => {
  it('rechaza un archivo que no es una imagen', async () => {
    const usuario = await renderizarFormulario()

    await usuario.upload(inputDeFoto(), archivoDe('lista-de-precios.pdf', 'application/pdf', 0.01))

    expect(
      screen.getByText('El archivo tiene que ser una imagen (JPG, PNG o WebP)')
    ).toBeInTheDocument()
    // Nada quedó cargado: sin foto no aparece el botón de quitarla.
    expect(screen.queryByRole('button', { name: 'Quitar foto' })).not.toBeInTheDocument()
    expect(inputDeFoto().files).toHaveLength(0)
  })

  it('rechaza una imagen de más de 5 MB y dice cuánto pesa', async () => {
    const usuario = await renderizarFormulario()

    await usuario.upload(inputDeFoto(), archivoDe('gigante.jpg', 'image/jpeg', 6))

    // El peso va en el mensaje a propósito: "es muy grande" no le dice a nadie
    // cuánto tiene que achicar la foto.
    expect(screen.getByText('La foto pesa 6.0 MB y el máximo es 5 MB')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quitar foto' })).not.toBeInTheDocument()
  })

  it('acepta una imagen dentro del tope', async () => {
    // El control del experimento: sin este, los dos de arriba pasarían igual si
    // la validación rechazara absolutamente todo.
    const usuario = await renderizarFormulario()

    await usuario.upload(inputDeFoto(), archivoDe('crema.jpg', 'image/jpeg', 2))

    expect(screen.queryByText(/tiene que ser una imagen/)).not.toBeInTheDocument()
    expect(screen.queryByText(/el máximo es 5 MB/)).not.toBeInTheDocument()
    // La vista previa se armó, que es lo que habilita quitarla.
    expect(screen.getByRole('button', { name: 'Quitar foto' })).toBeInTheDocument()
  })
})
