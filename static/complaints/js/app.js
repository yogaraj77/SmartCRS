document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.getElementById("menuBtn");
  const sidebar = document.getElementById("sidebar");

  if (menuBtn && sidebar) {
    menuBtn.addEventListener("click", () => {
      sidebar.classList.toggle("active");
      const icon = menuBtn.querySelector("i");
      if (icon) {
        icon.classList.toggle("fa-bars");
        icon.classList.toggle("fa-xmark");
      }
    });
  }

  const profile = document.getElementById("profile");
  const dropdown = document.getElementById("dropdown");

  if (profile && dropdown) {
    profile.addEventListener("click", (event) => {
      event.stopPropagation();
      dropdown.classList.toggle("active");
    });

    document.addEventListener("click", () => {
      dropdown.classList.remove("active");
    });
  }

  document.querySelectorAll(".message").forEach((message) => {
    window.setTimeout(() => {
      message.style.opacity = "0";
      message.style.transform = "translateY(-8px)";
    }, 4500);
  });

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    const userIdInput = loginForm.querySelector('input[name="user_id"]');
    const roleInputs = loginForm.querySelectorAll('input[name="role"]');
    const signupPrompt = document.getElementById("signupPrompt");
    const signupLink = document.getElementById("signupLink");
    const placeholders = {
      student: "Enter Student ID",
      staff: "Enter Faculty ID",
      admin: "Enter Admin Username",
    };

    const updateLoginRoleUi = (role) => {
      if (userIdInput) {
        userIdInput.placeholder = placeholders[role] || "Enter User ID";
      }

      if (!signupPrompt || !signupLink) {
        return;
      }

      if (role === "student") {
        signupPrompt.style.display = "";
        signupLink.href = signupLink.dataset.studentUrl;
      } else if (role === "staff") {
        signupPrompt.style.display = "";
        signupLink.href = signupLink.dataset.facultyUrl;
      } else if (role === "admin") {
        signupPrompt.style.display = "";
        signupLink.href = signupLink.dataset.adminUrl;
      }
    };

    roleInputs.forEach((input) => {
      input.addEventListener("change", () => {
        updateLoginRoleUi(input.value);
      });
    });

    const selectedRole = loginForm.querySelector('input[name="role"]:checked');
    if (selectedRole) {
      updateLoginRoleUi(selectedRole.value);
    }
  }

  const descriptionInput = document.getElementById("descriptionInput");
  const charCount = document.getElementById("charCount");

  if (descriptionInput && charCount) {
    const updateCount = () => {
      charCount.textContent = descriptionInput.value.length;
    };
    updateCount();
    descriptionInput.addEventListener("input", updateCount);
  }

  const complaintForm = document.getElementById("complaintForm");
  const draftBtn = document.getElementById("draftBtn");
  const draftKey = "smartComplaintDraft";

  if (complaintForm) {
    const loadDraft = () => {
      const rawDraft = localStorage.getItem(draftKey);
      if (!rawDraft) {
        return;
      }

      try {
        const draft = JSON.parse(rawDraft);
        Object.entries(draft).forEach(([name, value]) => {
          const field = complaintForm.elements[name];
          if (field && field.type !== "file") {
            field.value = value;
          }
        });
        if (descriptionInput && charCount) {
          charCount.textContent = descriptionInput.value.length;
        }
      } catch (_error) {
        localStorage.removeItem(draftKey);
      }
    };

    const saveDraft = () => {
      const formData = new FormData(complaintForm);
      const draft = {};
      formData.forEach((value, key) => {
        if (key !== "csrfmiddlewaretoken" && key !== "attachment") {
          draft[key] = value;
        }
      });
      localStorage.setItem(draftKey, JSON.stringify(draft));
    };

    loadDraft();

    if (draftBtn) {
      draftBtn.addEventListener("click", () => {
        saveDraft();
        draftBtn.classList.add("saved");
        draftBtn.innerHTML = '<i class="fa-solid fa-check"></i> Draft Saved';
        window.setTimeout(() => {
          draftBtn.classList.remove("saved");
          draftBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Draft';
        }, 1800);
      });
    }

    complaintForm.addEventListener("submit", () => {
      localStorage.removeItem(draftKey);
    });
  }

  document.querySelectorAll("[data-tag]").forEach((tag) => {
    tag.addEventListener("click", () => {
      if (!descriptionInput) {
        return;
      }
      const text = tag.dataset.tag || tag.textContent.trim();
      const prefix = descriptionInput.value.trim();
      descriptionInput.value = prefix ? `${prefix}\n${text}` : text;
      descriptionInput.dispatchEvent(new Event("input"));
      descriptionInput.focus();
    });
  });

  const passwordInput = document.getElementById("passwordStrengthInput");
  const passwordText = document.getElementById("passwordStrengthText");

  if (passwordInput && passwordText) {
    passwordInput.addEventListener("input", () => {
      const length = passwordInput.value.length;
      if (length === 0) {
        passwordText.textContent = "Password strength";
        passwordText.style.color = "";
      } else if (length < 6) {
        passwordText.textContent = "Weak password";
        passwordText.style.color = "#ef4444";
      } else if (length < 9) {
        passwordText.textContent = "Medium password";
        passwordText.style.color = "#f59e0b";
      } else {
        passwordText.textContent = "Strong password";
        passwordText.style.color = "#22c55e";
      }
    });
  }

  document.querySelectorAll(".detail-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.target;
      const card = button.closest(".complaint-card");
      const target = document.getElementById(targetId);

      if (!target || !card) {
        return;
      }

      card.querySelectorAll(".inline-panel").forEach((panel) => {
        if (panel !== target) {
          panel.classList.remove("active");
        }
      });

      target.classList.toggle("active");
    });
  });
});
