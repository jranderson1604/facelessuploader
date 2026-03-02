// Faceless Shorts Dashboard JS

document.addEventListener("DOMContentLoaded", () => {
  // Load stats
  fetch("/status")
    .then((r) => r.json())
    .then((data) => {
      const el = document.getElementById("videos-count");
      if (el) el.textContent = data.videos_on_disk;
    })
    .catch(() => {});

  // URL form
  const urlForm = document.getElementById("url-form");
  if (urlForm) {
    urlForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const result = document.getElementById("url-result");
      const formData = new FormData(urlForm);

      result.className = "result show success";
      result.textContent = "Processing... this may take a few minutes.";

      try {
        const resp = await fetch("/generate", { method: "POST", body: formData });
        const data = await resp.json();
        if (resp.ok) {
          result.className = "result show success";
          result.textContent = data.message;
        } else {
          result.className = "result show error";
          result.textContent = data.error || "Something went wrong";
        }
      } catch (err) {
        result.className = "result show error";
        result.textContent = "Request failed: " + err.message;
      }
    });
  }

  // Auto form
  const autoForm = document.getElementById("auto-form");
  if (autoForm) {
    autoForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const result = document.getElementById("auto-result");
      const formData = new FormData(autoForm);

      result.className = "result show success";
      result.textContent = "Starting auto-generation...";

      try {
        const resp = await fetch("/auto", { method: "POST", body: formData });
        const data = await resp.json();
        if (resp.ok) {
          result.className = "result show success";
          result.textContent = data.message;
        } else {
          result.className = "result show error";
          result.textContent = data.error || "Something went wrong";
        }
      } catch (err) {
        result.className = "result show error";
        result.textContent = "Request failed: " + err.message;
      }
    });
  }
});
