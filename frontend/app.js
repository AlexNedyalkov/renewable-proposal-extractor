const form = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const loading = document.getElementById('loading');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  loading.hidden = false;

  try {
    const response = await fetch('/api/documents', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    // Results/error rendering is added in later sprint v2 tasks.
    console.log(data);
  } finally {
    loading.hidden = true;
  }
});
