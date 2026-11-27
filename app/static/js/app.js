function showAlert(icon, message) {
  return Swal.fire({
    icon,
    text: message,
    confirmButtonText: 'Aceptar',
    confirmButtonColor: '#3858d6'
  });
}

async function apiFetch(url, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});
  const token = document.querySelector('meta[name="csrf-token"]')?.content;

  if (token && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRFToken', token);
  }
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response;
  try {
    response = await fetch(url, {...options, method, headers});
  } catch (error) {
    await showAlert('error', 'No fue posible conectar con el servidor.');
    throw error;
  }

  const data = await response.json().catch(() => ({
    ok: false,
    message: 'El servidor devolvió una respuesta no válida.'
  }));

  if (response.status === 401) {
    window.location.href = '/login';
  }
  return {response, data};
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('table.datatable').forEach(table => {
    if (window.DataTable) {
      new DataTable(table, {
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        order: [],
        language: {
          url: 'https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json'
        }
      });
    }
  });
});
