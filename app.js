document.addEventListener("DOMContentLoaded", () => {
  // Dismiss flash messages.
  document.querySelectorAll(".flash-close").forEach(button => {
    button.addEventListener("click", () => button.parentElement.remove());
  });

  // Confirm destructive actions.
  document.querySelectorAll("form[data-confirm]").forEach(form => {
    form.addEventListener("submit", event => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  // Small entrance animation using IntersectionObserver.
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });
  document.querySelectorAll(".reveal").forEach(card => observer.observe(card));

  // Preview uploaded poster before submitting.
  const upload = document.querySelector('input[name="poster"]');
  const preview = document.getElementById("imagePreview");
  if (upload && preview) {
    upload.addEventListener("change", () => {
      const file = upload.files[0];
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        preview.textContent = "Please choose an image file.";
        return;
      }
      const reader = new FileReader();
      reader.onload = event => {
        preview.innerHTML = "";
        const image = document.createElement("img");
        image.src = event.target.result;
        image.alt = "Selected poster preview";
        preview.appendChild(image);
      };
      reader.readAsDataURL(file);
    });
  }

  // Preview a remote poster URL in the add/edit form.
  const imageUrl = document.querySelector('input[name="image_url"]');
  if (imageUrl && preview) {
    imageUrl.addEventListener("change", () => {
      if (!imageUrl.value) return;
      const image = document.createElement("img");
      image.alt = "Poster URL preview";
      image.src = imageUrl.value;
      image.onerror = () => { preview.textContent = "Could not load that image URL."; };
      preview.innerHTML = "";
      preview.appendChild(image);
    });
  }
});
