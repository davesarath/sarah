
document.addEventListener("DOMContentLoaded", function () {
  const sidebarToggle = document.querySelector("#sidebarToggle");
  const sidebar = document.querySelector(".admin-sidebar");

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function () {
      sidebar.classList.toggle("active");
    });
  }
});


function confirmLogout(event) {
  event.preventDefault();
  if (confirm("Are you sure you want to log out?")) {
    window.location.href = "index.html"; 
  }
}


function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener("submit", function (e) {
    let valid = true;
    const inputs = form.querySelectorAll("input[required], select[required], textarea[required]");

    inputs.forEach(input => {
      if (!input.value.trim()) {
        valid = false;
        input.classList.add("is-invalid");
      } else {
        input.classList.remove("is-invalid");
      }
    });

    if (!valid) {
      e.preventDefault();
      alert("⚠️ Please fill in all required fields.");
    }
  });
}


validateForm("registerForm");
validateForm("addMedicalForm");
validateForm("vaccinationForm");


function showToast(message, type = "success") {
  const toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) return;

  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-bg-${type} border-0`;
  toast.role = "alert";
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  toastContainer.appendChild(toast);

  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();

  toast.addEventListener("hidden.bs.toast", () => {
    toast.remove();
  });
}
