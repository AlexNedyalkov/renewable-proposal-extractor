const form = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const lookupForm = document.getElementById('lookup-form');
const lookupIdInput = document.getElementById('lookup-id-input');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const validationError = document.getElementById('validation-error');
const errorBanner = document.getElementById('error-banner');
const emptyState = document.getElementById('empty-state');

function showValidationError(message) {
  validationError.textContent = message;
  validationError.hidden = false;
}

function clearValidationError() {
  validationError.hidden = true;
  validationError.textContent = '';
}

function showErrorBanner(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
}

function clearErrorBanner() {
  errorBanner.hidden = true;
  errorBanner.textContent = '';
}

function humanizeFieldName(fieldName) {
  return fieldName
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function renderResults(extraction) {
  results.innerHTML = '';

  for (const [fieldName, field] of Object.entries(extraction)) {
    const notFound = field.confidence === 'not_found';

    const fieldEl = document.createElement('div');
    fieldEl.className = 'field' + (notFound ? ' field-not-found' : '');
    fieldEl.dataset.testid = `field-${fieldName}`;

    const labelEl = document.createElement('div');
    labelEl.className = 'field-label';
    labelEl.textContent = humanizeFieldName(fieldName);
    fieldEl.appendChild(labelEl);

    const valueEl = document.createElement('div');
    valueEl.className = 'field-value' + (notFound ? ' field-value-not-found' : '');
    valueEl.dataset.testid = `field-${fieldName}-value`;
    valueEl.textContent = notFound ? 'Not found in document' : String(field.value);
    fieldEl.appendChild(valueEl);

    const confidenceEl = document.createElement('span');
    confidenceEl.className = `confidence-badge confidence-${field.confidence}`;
    confidenceEl.dataset.testid = `field-${fieldName}-confidence`;
    confidenceEl.textContent = field.confidence;
    fieldEl.appendChild(confidenceEl);

    if (field.source_snippet) {
      const snippetEl = document.createElement('div');
      snippetEl.className = 'field-snippet';
      snippetEl.dataset.testid = `field-${fieldName}-snippet`;
      snippetEl.textContent = `"${field.source_snippet}"`;
      fieldEl.appendChild(snippetEl);
    }

    results.appendChild(fieldEl);
  }

  results.hidden = false;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    showValidationError('Please select a PDF file to upload.');
    return;
  }

  // Client-side UX nicety only, not a security boundary — the backend's
  // magic-byte check is the real gate against malformed/spoofed uploads.
  if (file.type !== 'application/pdf') {
    showValidationError('Only PDF files are supported.');
    return;
  }

  clearValidationError();
  clearErrorBanner();
  emptyState.hidden = true;

  const formData = new FormData();
  formData.append('file', file);

  loading.hidden = false;

  try {
    const response = await fetch('/api/documents', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();

    if (response.ok) {
      renderResults(data.extraction);
    } else {
      const message = data?.detail?.message || 'An unexpected error occurred.';
      showErrorBanner(message);
      console.error(data);
    }
  } finally {
    loading.hidden = true;
  }
});

lookupForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const documentId = lookupIdInput.value.trim();
  if (!documentId) {
    showValidationError('Please enter a document ID to look up.');
    return;
  }

  clearValidationError();
  clearErrorBanner();
  emptyState.hidden = true;

  loading.hidden = false;

  try {
    const response = await fetch(`/api/documents/${encodeURIComponent(documentId)}`);
    const data = await response.json();

    if (response.ok) {
      renderResults(data.extraction);
    } else {
      const message = data?.detail?.message || 'An unexpected error occurred.';
      showErrorBanner(message);
      console.error(data);
    }
  } finally {
    loading.hidden = true;
  }
});
