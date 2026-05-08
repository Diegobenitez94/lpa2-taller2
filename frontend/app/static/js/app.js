const form = document.getElementById('invoice-form');
const status = document.getElementById('status');
const submitButton = form?.querySelector('button[type="submit"]');

const setStatus = (message, type = 'info') => {
    if (!status) return;
    status.textContent = message;
    status.className = 'status';
    if (type === 'error') {
        status.classList.add('status--error');
    } else if (type === 'success') {
        status.classList.add('status--success');
    }
};

const setLoading = (loading) => {
    if (!submitButton) return;
    submitButton.disabled = loading;
    submitButton.textContent = loading ? 'Generando...' : 'Generar PDF';
};

const downloadBlob = async (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
};

const parseErrorMessage = async (response) => {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        const data = await response.json();
        return data.error || data.detail || data.message || 'Error desconocido';
    }
    return response.statusText || 'Error desconocido';
};

const validateInvoiceId = async (invoiceId) => {
    try {
        const response = await fetch(`/api/facturas/${invoiceId}`);
        if (!response.ok) {
            const message = await parseErrorMessage(response);
            return { valid: false, error: message };
        }
        return { valid: true, data: await response.json() };
    } catch (error) {
        return { valid: false, error: 'No se pudo verificar la factura' };
    }
};

if (form) {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        setStatus('');

        const invoiceId = form.querySelector('#id_factura')?.value.trim();
        if (!invoiceId) {
            setStatus('Ingresa un ID de factura válido.', 'error');
            return;
        }

        setLoading(true);
        try {
            setStatus('Validando factura...');
            const validation = await validateInvoiceId(invoiceId);
            if (!validation.valid) {
                setStatus(validation.error, 'error');
                setLoading(false);
                return;
            }

            setStatus('Generando PDF...');
            const formData = new FormData();
            formData.append('id_factura', invoiceId);

            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorMessage = await parseErrorMessage(response);
                setStatus(errorMessage || `Error ${response.status}: no se pudo generar la factura.`, 'error');
                return;
            }

            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/pdf')) {
                const blob = await response.blob();
                await downloadBlob(blob, `Factura_${invoiceId}.pdf`);
                setStatus('Factura generada correctamente. Revisa tu descarga.', 'success');
            } else {
                setStatus('Respuesta inesperada del servidor.', 'error');
            }
        } catch (error) {
            setStatus('No se pudo conectar con el servidor. Intenta de nuevo más tarde.', 'error');
            console.error(error);
        } finally {
            setLoading(false);
        }
    });
}

