function isValidUrl(string) {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
}

async function shortenUrl() {
  const url = document.getElementById('urlInput').value;
  console.log('Button clicked, URL:', url);
  if (!url) {
    document.getElementById('result').innerHTML = '<p style="color: red;">Please enter a URL</p>';
    return;
  }
  if (!isValidUrl(url)) {
    document.getElementById('result').innerHTML = '<p style="color: red;">Please enter a valid URL</p>';
    return;
  }
  try {
    console.log('Sending request to /api/shorten');
    const response = await fetch('/api/shorten', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    console.log('Response status:', response.status);
    const data = await response.json();
    console.log('Response data:', data);
    if (data.short_url) {
      document.getElementById('result').innerHTML = `
        <p>Short URL: <a href="${data.short_url}" target="_blank">${data.short_url}</a></p>
        <button onclick="copyToClipboard('${data.short_url}')">Copy</button>
      `;
    } else {
      document.getElementById('result').innerHTML = '<p style="color: red;">Error: ' + (data.detail || 'Unknown error') + '</p>';
    }
  } catch (error) {
    console.log('Fetch error:', error);
    document.getElementById('result').innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showNotification('Ссылка скопирована!');
  }).catch(err => {
    console.error('Failed to copy: ', err);
    showNotification('Ошибка копирования', true);
  });
}

function showNotification(message, isError = false) {
  const notification = document.createElement('div');
  notification.textContent = message;
  notification.style.position = 'fixed';
  notification.style.top = '20px';
  notification.style.right = '20px';
  notification.style.backgroundColor = isError ? '#dc3545' : '#28a745';
  notification.style.color = 'white';
  notification.style.padding = '10px 20px';
  notification.style.borderRadius = '4px';
  notification.style.zIndex = '1000';
  notification.style.fontSize = '14px';
  document.body.appendChild(notification);
  setTimeout(() => {
    document.body.removeChild(notification);
  }, 1000);
}