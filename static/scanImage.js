let lock = false;

async function submitImageForm(image) {
  if (lock) return;
  lock = true;

  const formData = new FormData();

  if (typeof image === 'string') {
    // If image is a URL
    formData.append('image_url', image);
  } else {
    // If image is a file
    formData.append('image', image);
  }

  try {
    const response = await fetch('/image', {
      method: 'POST',
      body: formData
    });

    const responseText = await response.text();

    // Function to insert HTML and execute script tags
    function insertHTMLWithScripts(html) {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;

      // Insert the new content
      document.body.innerHTML = tempDiv.innerHTML;

      // Find and evaluate all script tags
      const scripts = tempDiv.getElementsByTagName('script');
      for (const script of scripts) {
        const newScript = document.createElement('script');
        if (script.src) {
          newScript.src = script.src;
        } else {
          newScript.textContent = script.textContent;
        }
        document.head.appendChild(newScript).parentNode.removeChild(newScript);
      }
    }

    // Insert the HTML and execute the scripts
    insertHTMLWithScripts(responseText);

    // Update the URL
    history.pushState(null, 'Image Upload', '/image');
  } catch (error) {
    console.error('Error:', error);
  }
}

function handleUploadFormSubmit(event) {
  event.preventDefault();
  const fileInput = document.getElementById('fileInput');
  if (fileInput.files.length > 0) {
    submitImageForm(fileInput.files[0]);
  }
}
